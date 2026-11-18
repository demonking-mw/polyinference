"""Offline graph and OS V1 checks; no local or cloud inference is started."""

import pytest
from langgraph.checkpoint.memory import InMemorySaver

from polyinference.config import Endpoint, RuntimeConfig
from polyinference.general_agents.graphs import BUILDERS, GraphContext
from polyinference.general_agents.os_v1 import run_v1
from polyinference.runtime import kernel
from polyinference.runtime.inference import HTTPInference
from polyinference.runtime.storage import Records


class ScriptedIO:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    async def model(self, role, phase, prompt, step):
        self.calls.append((role, phase, step))
        return next(self.replies)

    async def lookup(self, query, step):
        self.calls.append(("lookup", query, step))
        return '{"hits":[{"source_id":"doc","excerpt":"the evidence"}]}'


@pytest.mark.parametrize("design,replies,roles", [
    ("simple", ['{"lookup":"evidence"}', '{"final":"done"}'], ["general", "lookup", "general"]),
    ("supervisor", ['{"tasks":["one","two"]}', "finding 1", "finding 2", "answer"],
     ["cloud", "local", "local", "cloud"]),
    ("research", ['{"questions":["one"]}', "doc supports the claim", "report [doc]"],
     ["cloud", "lookup", "local", "cloud"]),
    ("writer", ['{"criteria":["clear"]}', "draft", '{"approved":false,"feedback":"shorter"}',
                "revised", '{"approved":true,"feedback":"ok"}'],
     ["cloud", "local", "cloud", "local", "cloud"]),
])
async def test_graphs_run_with_plain_langgraph(design, replies, roles):
    io = ScriptedIO(replies)
    result = await BUILDERS[design]().ainvoke({"task": "task"}, context=GraphContext(io))
    assert result["answer"]
    assert [item[0] for item in io.calls] == roles


async def test_simple_graph_uses_v1_journal_and_replays(tmp_path, monkeypatch):
    # Use the real OS journal. A fresh graph saver on the second invocation
    # forces receipt replay without this host's stalled async SQLite worker.
    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

    monkeypatch.setattr(kernel.aiosqlite, "connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(kernel, "AsyncSqliteSaver", lambda _connection: InMemorySaver())
    calls = []

    async def generate(self, messages, max_output, response_schema=None, **kwargs):
        calls.append(messages)
        text = '{"lookup":"fact"}' if len(calls) == 1 else '{"final":"answer [doc]"}'
        return {"text": text, "model": "fixture", "usage": {"total_tokens": 5}}

    monkeypatch.setattr(HTTPInference, "generate", generate)
    endpoint = Endpoint(model="fixture", base_url="http://fixture/v1", protocol="chat")
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
        local=endpoint, cloud=endpoint, role_bindings={"general": "cloud", "local": "local", "cloud": "cloud"},
        prepare_repository=False, checks=[], allowed_write_paths=[])
    first = await run_v1("simple", config, "Find fact", {"doc": "fact is true"})
    second = await run_v1("simple", config, "Find fact", {"doc": "fact is true"})
    assert first == second
    assert len(calls) == 2
    records = Records(config.state_path / "records.sqlite")
    try:
        assert len(records.scan("effect/")) == 3
        assert len(records.scan("process-spec/")) == 3
        assert all(row[2]["state"] == "succeeded" for row in records.scan("effect/"))
        assert not records.scan("task/")
    finally:
        records.db.close()
    assert not (tmp_path / "unused").exists()


async def test_multi_level_rejects_unverified_role_placement(tmp_path):
    endpoint = Endpoint(model="fixture", base_url="http://fixture/v1", protocol="chat")
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
        local=endpoint, cloud=endpoint, role_bindings={"local": "local", "cloud": "cloud"})
    with pytest.raises(ValueError, match="distinct endpoints explicitly declared"):
        await run_v1("supervisor", config, "task")
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("design,replies,effects", [
    ("supervisor", ['{"tasks":["one"]}', "finding", "answer"], 3),
    ("research", ['{"questions":["fact"]}', "finding [doc]", "report [doc]"], 4),
    ("writer", ['{"criteria":["clear"]}', "draft", '{"approved":true,"feedback":"ok"}'], 3),
])
async def test_multi_level_graphs_use_distinct_v1_roles(tmp_path, monkeypatch, design, replies, effects):
    class Connection:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return None

    monkeypatch.setattr(kernel.aiosqlite, "connect", lambda *_args, **_kwargs: Connection())
    monkeypatch.setattr(kernel, "AsyncSqliteSaver", lambda _connection: InMemorySaver())
    script = iter(replies)
    calls = []

    async def generate(self, messages, max_output, response_schema=None, **kwargs):
        calls.append(self.endpoint.inference_location)
        return {"text": next(script), "model": "fixture", "usage": {"total_tokens": 5}}

    monkeypatch.setattr(HTTPInference, "generate", generate)
    local = Endpoint(model="fixture-local", base_url="http://fixture/v1", protocol="chat",
                     inference_location="local")
    cloud = Endpoint(model="fixture-cloud", base_url="http://fixture/v1", protocol="chat",
                     inference_location="cloud")
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
        local=local, cloud=cloud, role_bindings={"local": "local", "cloud": "cloud"},
        prepare_repository=False, checks=[], allowed_write_paths=[])
    first = await run_v1(design, config, "Find fact", {"doc": "fact is true"})
    second = await run_v1(design, config, "Find fact", {"doc": "fact is true"})
    assert first == second
    assert calls[0] == "cloud" and "local" in calls
    records = Records(config.state_path / "records.sqlite")
    try:
        assert len(records.scan("effect/")) == effects
        assert all(row[2]["state"] == "succeeded" for row in records.scan("effect/"))
    finally:
        records.db.close()



async def test_research_repairs_an_overlong_plan_at_most_once():
    import json

    from polyinference.general_agents.graphs import MAX_PLAN_ITEM_CHARS

    overlong = json.dumps({"questions": ["x" * (MAX_PLAN_ITEM_CHARS + 1)]})
    good = json.dumps({"questions": ["usable evidence"]})
    graph = BUILDERS["research"]()
    io = ScriptedIO([overlong, good, "finding [doc]", "answer [doc]"])
    result = await graph.ainvoke({"task": "Find the evidence"}, context=GraphContext(io))
    assert result["answer"] == "answer [doc]"
    assert io.calls[:3] == [
        ("cloud", "research_plan", "plan"),
        ("cloud", "research_plan", "plan-repair"),
        ("lookup", "usable evidence", "evidence-0"),
    ]

    invalid = ScriptedIO([overlong, overlong])
    with pytest.raises(ValueError, match="invalid after one correction"):
        await graph.ainvoke({"task": "Find the evidence"}, context=GraphContext(invalid))
    assert [call[2] for call in invalid.calls] == ["plan", "plan-repair"]


def test_lookup_returned_excerpt_covers_match_beyond_document_prefix():
    from polyinference.general_agents.os_v1 import _search

    passage = "The queue timeout is 35 milliseconds."
    docs = {"manual": "Unrelated instructions. " * 150 + passage, "other": "General overview."}
    result = _search(docs, "queue timeout")
    assert [hit["source_id"] for hit in result["hits"]] == ["manual"]
    excerpt = result["hits"][0]["excerpt"]
    assert passage in excerpt
    assert len(excerpt) <= 2000 and excerpt in docs["manual"]


async def test_batch_shares_one_kernel_and_isolates_corpora_and_replay(tmp_path, monkeypatch):
    import asyncio
    import json
    from collections import Counter

    from polyinference.general_agents.os_v1 import BatchInvocation, run_v1_batch

    local = Endpoint(model="local-fixture", inference_location="local", max_inflight=1)
    cloud = Endpoint(model="cloud-fixture", inference_location="cloud", max_inflight=1)
    config = RuntimeConfig(repository=str(tmp_path / "unused"), state_directory=str(tmp_path / "state"),
        local=local, cloud=cloud, role_bindings={"general": "cloud", "local": "local", "cloud": "cloud"},
        prepare_repository=False, checks=[], allowed_write_paths=[], max_workers=4)
    opens = []
    open_kernel = kernel.KernelRuntime.open

    async def count_open(self):
        opens.append(self.config.state_path)
        return await open_kernel(self)

    monkeypatch.setattr(kernel.KernelRuntime, "open", count_open)
    active, peaks = Counter(), Counter()
    calls = []

    async def generate(self, messages, _max_output, _response_schema=None, **kwargs):
        model = self.endpoint.model
        active[model] += 1
        peaks[model] = max(peaks[model], active[model])
        try:
            await asyncio.sleep(.015)
            payload = json.dumps(messages)
            calls.append((model, payload))
            if "Research task:" in payload:
                reply = '{"questions":["ledger"]}'
            elif "Extract only claims" in payload:
                marker, = [value for value in ("CEDAR", "MARBLE") if value in payload]
                assert model == "local-fixture"
                reply = marker
            elif "Answer using the findings only" in payload:
                marker, = [value for value in ("CEDAR", "MARBLE") if value in payload]
                assert model == "cloud-fixture"
                reply = marker
            elif "Previous observation: none" in payload:
                reply = '{"lookup":"ledger"}'
            else:
                marker, = [value for value in ("ORCHID", "JASPER") if value in payload]
                assert model == ("cloud-fixture" if marker == "ORCHID" else "local-fixture")
                reply = json.dumps({"final": marker})
            return {"text": reply, "model": model, "usage": {"total_tokens": 5}}
        finally:
            active[model] -= 1

    monkeypatch.setattr(HTTPInference, "generate", generate)
    manifest = [
        BatchInvocation(id="ra", design="research", task="Task A", documents={"ledger": "ledger CEDAR"}),
        BatchInvocation(id="rb", design="research", task="Task B", documents={"ledger": "ledger MARBLE"}),
        BatchInvocation(id="sc", design="simple", binding="cloud", task="Task C",
                        documents={"ledger": "ledger ORCHID"}),
        BatchInvocation(id="sl", design="simple", binding="local", task="Task D",
                        documents={"ledger": "ledger JASPER"}),
    ]
    first = await run_v1_batch(config, manifest)
    assert opens == [config.state_path]
    assert [row.get("answer") for row in first] == ["CEDAR", "MARBLE", "ORCHID", "JASPER"], first
    assert peaks == {"cloud-fixture": 1, "local-fixture": 1}
    assert len(calls) == 10
    assert await run_v1_batch(config, manifest) == first
    assert len(calls) == 10

    changed = [manifest[0].model_copy(update={"task": "Changed"}), *manifest[1:]]
    with pytest.raises(ValueError, match="Saved agent batch changed"):
        await run_v1_batch(config, changed)
    with pytest.raises(ValueError, match="IDs must be unique"):
        await run_v1_batch(config, [manifest[0], manifest[0]])

    records = Records(config.state_path / "records.sqlite")
    try:
        assert len(records.scan("effect/")) == 14
        assert all(body["state"] == "succeeded" for _, _, body in records.scan("effect/"))
        assert all(body["state"] == "released" for _, _, body in records.scan("reservation/"))
        assert len({k for k, _, _ in records.scan("runtime/capability/sources.lookup.")}) == 4
    finally:
        records.db.close()
