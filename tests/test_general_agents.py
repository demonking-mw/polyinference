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
