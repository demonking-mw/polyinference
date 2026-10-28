"""Source-grounded regressions for the four scheduled repairs; no live inference."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from polyinference.agent.worker_memory import LIMIT, project
from polyinference.primitives import canonical


class Records:
    def __init__(self):
        self.rows = {}

    def get(self, key):
        return self.rows.get(key)

    def compare_and_publish(self, expected, updates):
        for key, value in updates.items():
            assert (self.rows.get(key) or (0,))[0] == expected[key]
            self.rows[key] = expected[key] + 1, deepcopy(value)


def memory_fixture():
    histories = {}
    records = Records()
    manifest = SimpleNamespace(generation=1)
    app = SimpleNamespace(
        ports=SimpleNamespace(records=records, workspaces=SimpleNamespace(current=lambda _: manifest)),
        history=lambda ref: histories.get(ref, []),
    )
    state = {
        "attempt_id": "a",
        "workspace_id": "ws",
        "process_id": "worker",
        "phase": "development",
        "trajectory_ref": "one",
    }
    code = {"effective_tree_digest": "tree", "environment_digest": "env"}
    return app, state, code, histories, manifest


def error(event="bad", tool="files.search", path="src/a.py"):
    return {
        "id": event,
        "reply": {"kind": "action", "tool": tool, "arguments": {"path": path}},
        "observation": {"error": "invalid path-shaped search"},
    }


def test_corrected_unscoped_search_retires_old_error_without_changing_history():
    app, state, code, histories, _ = memory_fixture()
    histories["one"] = [error()]
    assert project(app, state, code)["errors"]
    histories["two"] = [
        *histories["one"],
        {
            "id": "corrected",
            "reply": {"kind": "action", "tool": "files.search", "arguments": {"pattern": "needle"}},
            "observation": {"matches": []},
        },
    ]
    state["trajectory_ref"] = "two"
    assert project(app, state, code)["errors"] == []
    revision = app.ports.records.get("worker-state/a")[0]
    assert project(app, state, code)["errors"] == []
    assert app.ports.records.get("worker-state/a")[0] == revision
    assert histories["one"][0]["observation"]["error"]
    state["trajectory_ref"] = "one"
    assert project(app, state, code)["errors"] == []
    assert app.ports.records.get("worker-state/a")[0] == revision


@pytest.mark.parametrize("kind", ["candidate", "assessment", "needs_review"])
def test_valid_non_action_reply_clears_protocol_error_with_no_observation(kind):
    app, state, code, histories, _ = memory_fixture()
    histories["one"] = [{"id": "protocol", "feedback": {"error": "bad phase reply"}}]
    assert project(app, state, code)["errors"][0]["kind"] == "protocol"
    histories["two"] = [*histories["one"], {"id": "valid", "reply": {"kind": kind}, "observation": None}]
    state["trajectory_ref"] = "two"
    assert project(app, state, code)["errors"] == []


def test_failed_correction_and_newer_error_are_not_cleared_by_replay():
    app, state, code, histories, _ = memory_fixture()
    histories["one"] = [error()]
    first = project(app, state, code)
    histories["two"] = [*histories["one"], error("newer")]
    state["trajectory_ref"] = "two"
    assert project(app, state, code)["errors"][-1]["event"] == "newer"
    state["trajectory_ref"] = "one"
    assert project(app, state, code)["errors"][-1]["event"] == "newer"
    assert first["errors"][0]["event"] == "bad"


def test_success_on_another_file_does_not_clear_an_unresolved_file_error():
    app, state, code, histories, _ = memory_fixture()
    histories["one"] = [error(tool="files.read")]
    project(app, state, code)
    histories["two"] = [
        *histories["one"],
        {
            "id": "other",
            "reply": {"kind": "action", "tool": "files.read", "arguments": {"path": "b.py"}},
            "observation": {"path": "b.py", "digest": "digest"},
        },
    ]
    state["trajectory_ref"] = "two"
    assert project(app, state, code)["errors"][0]["path"] == "src/a.py"


def test_generation_invalidates_cas_facts_and_keeps_projection_bounded():
    app, state, code, histories, manifest = memory_fixture()
    histories["one"] = [
        {
            "id": "read",
            "reply": {"kind": "action", "tool": "files.read"},
            "observation": {"path": "a.py", "digest": "old"},
        }
    ]
    assert project(app, state, code)["files"]
    manifest.generation += 1
    current = project(app, state, code)
    assert current["files"] == {} and len(canonical(current)) <= LIMIT
    assert histories["one"][0]["observation"]["digest"] == "old"


async def test_measured_tokens_use_64k_window_and_actual_raw_output_reserve(tmp_path):
    import json

    import httpx
    from test_context_safety import part, with_parts
    from test_model_retries import body, install, setup

    from polyinference.primitives import operation_fingerprint, runtime_limits

    limits = runtime_limits().model_copy(
        update={"max_input_tokens_per_call": 400000, "max_output_tokens_per_call": 16384}
    )
    rt, request = await setup(
        tmp_path,
        protocol="chat",
        endpoint_options={
            "max_context_tokens": 65536,
            "reserved_context_tokens": 65536,
            "input_token_count_path": "/chat/completions/input_tokens",
        },
        limits=limits,
    )
    request = request.model_copy(
        update={
            "payload": request.payload.model_copy(
                update={
                    "context": request.payload.context.model_copy(update={"maximum_input_tokens": 400000})
                }
            ),
            "extensions": {"runtime/output-tokens": 4096},
        }
    )
    request = with_parts(rt, request, [part(rt, request, "large", "useful source " * 9000)])
    request = request.model_copy(update={"intent_digest": operation_fingerprint(request)})
    calls = []

    async def handler(req):
        wire = json.loads(req.content)
        calls.append((req.url.path, wire))
        return httpx.Response(
            200,
            json={"input_tokens": 30000} if req.url.path.endswith("input_tokens") else body("chat", "done"),
        )

    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded"
        receipt = result.extensions["runtime/context-receipt"]
        assert receipt["input_allowance"] == 61440 and receipt["output_reservation_tokens"] == 4096
        assert receipt["submitted_bytes"] > 100000 and receipt["submitted_input_tokens"] == 30000
        assert receipt["measurement_provenance"] == "provider_reported" and not receipt["omitted_refs"]
        assert calls[0][1] == calls[-1][1] and len(calls) == 2
        assert rt.inference_calls_used("research") == 1 and not rt.config.repo_path.exists()
    finally:
        await rt.close()


@pytest.mark.parametrize("response", [{"input_tokens": True}, {"input_tokens": -1}, {"unavailable": True}])
async def test_invalid_counter_falls_back_to_a_labeled_bound(tmp_path, response):
    import httpx
    from test_model_retries import body, install, setup

    rt, request = await setup(
        tmp_path,
        protocol="chat",
        endpoint_options={"input_token_count_path": "/chat/completions/input_tokens"},
    )
    calls = []

    async def handler(req):
        calls.append(req.url.path)
        return httpx.Response(
            200, json=response if req.url.path.endswith("input_tokens") else body("chat", "done")
        )

    await install(rt, request, handler)
    try:
        result = await rt.execute(request)
        assert result.state == "succeeded"
        receipt = result.extensions["runtime/context-receipt"]
        assert receipt["measurement_provenance"] == "conservative_bytes" and receipt["measurement_issue"]
        assert receipt["submitted_input_tokens"] == receipt["submitted_bytes"]
    finally:
        await rt.close()


async def test_byte_ceiling_cannot_be_bypassed_by_token_counter(tmp_path):
    import httpx
    from test_context_safety import part, with_parts
    from test_model_retries import install, setup

    rt, request = await setup(
        tmp_path,
        protocol="chat",
        max_model_request_bytes=1000,
        endpoint_options={"input_token_count_path": "/chat/completions/input_tokens"},
    )
    request = with_parts(rt, request, [part(rt, request, "big", "x" * 2000)])
    calls = []

    async def handler(req):
        calls.append(req.url.path)
        return httpx.Response(200, json={"input_tokens": 1})

    await install(rt, request, handler)
    try:
        assert (await rt.execute(request)).state == "failed"
        assert not calls and rt.inference_calls_used("research") == 0
        assert rt.records.get("context-receipt/summary")[1]["max_request_bytes"] == 1000
    finally:
        await rt.close()


async def test_caller_priority_preserves_whole_groups_without_semantics(tmp_path):
    import json

    import httpx
    from test_context_safety import part, with_parts
    from test_model_retries import body, install, setup

    from polyinference.primitives import runtime_limits

    rt, request = await setup(
        tmp_path,
        protocol="chat",
        max_model_request_bytes=100000,
        limits=runtime_limits().model_copy(update={"max_input_tokens_per_call": 1000}),
        endpoint_options={"input_token_count_path": "/chat/completions/input_tokens"},
    )
    important = part(rt, request, "first", "x" * 3000, required=False).model_copy(
        update={"retention_priority": 90}
    )
    call = part(rt, request, "pair-call", "x" * 1500, required=False, kind="tool_call", call_id="pair")
    result = part(rt, request, "pair-result", "x" * 1500, required=False, kind="tool_result", call_id="pair")
    other = part(rt, request, "later", "x" * 3000, required=False)
    request = with_parts(
        rt,
        request,
        [part(rt, request, "pin", "Required"), important, call, result, other],
        {"auto_deal_context": True},
    )

    async def handler(req):
        wire = json.loads(req.content)
        return httpx.Response(
            200,
            json={"input_tokens": sum(len(m["content"]) for m in wire["messages"]) // 8 + 10}
            if req.url.path.endswith("input_tokens")
            else body("chat", "done"),
        )

    await install(rt, request, handler)
    try:
        response = await rt.execute(request)
        assert response.state == "succeeded"
        assert response.extensions["runtime/context-receipt"]["omitted_refs"] == ["pair-call", "pair-result"]
    finally:
        await rt.close()


def test_failure_source_previews_prefer_the_entry_and_test_over_alphabetic_noise():
    from polyinference.agent.diagnostics import source_previews
    from polyinference.execution_contracts import Check

    tree = {
        **{f"aaa-{i}.js": ("100644", b"unrelated" * 100) for i in range(20)},
        "src/main.js": ("100644", b"entry integration"),
        "tests/entry.test.js": ("100644", b"failed behavior test"),
    }
    selected = source_previews(
        tree,
        {"write_paths": ["src/main.js"], "checks": ["unit"]},
        [Check(name="unit", argv=["node", "--test", "tests/entry.test.js"])],
        "tests/entry.test.js:1: failed",
    )
    assert [p["path"] for p in selected] == ["tests/entry.test.js", "src/main.js"]


def test_search_novelty_uses_discovered_source_not_renamed_queries():
    from polyinference.agent.progress import observe_tool

    first = {"matches": [{"path": "a.py", "line": 3, "text": "source"}]}
    assert observe_tool("files.search", {"pattern": "one"}, first, {}) == observe_tool(
        "files.search", {"pattern": "two"}, first, {}
    )
    assert observe_tool("files.search", {"pattern": "new"}, {"matches": []}, {}) == []
    assert observe_tool(
        "files.search", {}, {"matches": [{"path": "a.py", "line": 4, "text": "new"}]}, {}
    ) != observe_tool("files.search", {}, first, {})


@pytest.mark.parametrize("code,reason", [("IncompleteGeneration", None),
    ("ModelResponseError", "unexpected_content"), ("NativeJobStopped", "invalid_native_output")])
async def test_clean_stopped_model_failure_parks_real_partial_source_for_semantic_review(config, code, reason):
    from test_exception_recovery import connect, seed

    from polyinference.agent.exceptions import park_model_failure, validate_allowance

    config = config.model_copy(
        update={"check_diagnosis": config.check_diagnosis.model_copy(update={"max_rounds": 0})}
    )
    rt, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        manifest = rt.workspaces.current(state["workspace_id"])
        root = rt.workspaces.root_for(manifest)
        (root / "a.py").write_text("VALUE = 7\n")
        await app.capability(
            state,
            "read-before-stop",
            "files.read",
            {"path": "a.py", "generation": manifest.generation},
            "read",
        )
        failure = {
            "operation_id": "failed-model",
            "error": {"code": code, "message": "unusable output"},
            "execution_termination": "confirmed_stopped",
            "effects": "known",
            "diagnostics": {"polyinference/model-output-error": {"reason": reason}} if reason else {},
        }
        before = rt.operations.resource_state(state["process_id"])
        assert await park_model_failure(app, state, failure)
        packet = app.get("worker-exception/" + state["attempt_id"])
        assert packet["model_failure"] == failure and packet["source_delta_ref"]
        assert packet["diagnosis"]["guidance"] == "Diagnostic allowance exhausted"
        assert not app.get(state["task_ledger_ref"]).get("report_ref")
        assert app.get(state["task_ledger_ref"])["model_failure"] is None
        validate_allowance(app, packet)
        after = rt.operations.resource_state(state["process_id"])
        assert before["remaining_model_calls"] == after["remaining_model_calls"]
        assert rt.records.get("exception-queue/" + state["attempt_id"])[1]["action"] == "pending"
        revision = rt.records.get(state["task_ledger_ref"])[0]
        assert await park_model_failure(app, state, failure)
        assert rt.records.get(state["task_ledger_ref"])[0] == revision
    finally:
        await rt.close()


@pytest.mark.parametrize(
    "change",
    [
        {"effects": "unknown"},
        {"execution_termination": "unknown"},
        {"diagnostics": {"polyinference/model-unavailable": True}},
        {"error": {"code": "ProviderError"}},
        {"error": {"code": "NativeJobStopped", "retryable_after_reconciliation": False}},
        {"error": {"code": "NativeJobStopped", "message": "RPC authentication rejection"}},
        {"error": {"code": "ModelResponseError"}, "diagnostics": {
            "polyinference/model-output-error": {"reason": "stop_reason", "stop_reason": "content_filter"}}},
    ],
)
async def test_model_semantic_handoff_never_reinterprets_unknown_or_provider_failures(config, change):
    from test_exception_recovery import connect, seed

    from polyinference.agent.exceptions import park_model_failure

    rt, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        failure = {
            "error": {"code": "IncompleteGeneration"},
            "effects": "known",
            "execution_termination": "confirmed_stopped",
            "diagnostics": {},
            **change,
        }
        assert not await park_model_failure(app, state, failure)
        assert not rt.records.scan("worker-exception/")
    finally:
        await rt.close()


@pytest.mark.parametrize("output_failure", [False, True])
async def test_native_adapter_facts_distinguish_provider_rejection_from_unusable_output(tmp_path, output_failure):
    from test_model_retries import setup

    from polyinference.runtime.codex import CodexAppServer, NativeJobStopped

    class Terminal(CodexAppServer):
        async def generate_job(self, *args, **kwargs):
            raise NativeJobStopped("fixture terminal failure", output_failure=output_failure)

    rt, request = await setup(tmp_path, protocol="codex_app_server", model_call_retries=0, max_model_recoveries=0,
        endpoint_options={"command": ["/nonexistent/pi-fixture-native-never-run"]})
    await rt.clients["local"].close()
    rt.clients["local"] = Terminal(rt.config.local)
    try:
        result = await rt.execute(request)
        assert result.state == "failed" and result.execution_termination == "confirmed_stopped"
        assert result.error.code == "NativeJobStopped" and rt.inference_calls_used("research") == 1
        assert result.error.message == "fixture terminal failure"
        detail = result.extensions.get("polyinference/model-output-error")
        assert (detail["reason"] == "invalid_native_output") if output_failure else detail is None
        assert not rt.uncertain()
    finally:
        await rt.close()


@pytest.mark.parametrize("blocker", ["cancel", "phase", "published", "calls", "tokens", "steps", "deadline"])
async def test_semantic_handoff_does_not_start_diagnosis_without_original_authority_and_allowance(config, monkeypatch, blocker):
    from datetime import datetime, timezone

    from test_exception_recovery import connect, seed

    from polyinference.agent.exceptions import park_model_failure

    rt, app, engine = await connect(config)
    try:
        state = await seed(app, engine)
        if blocker == "cancel":
            app.update("process-control/" + state["process_id"], {"cancel_requested": True})
        elif blocker == "phase":
            state["phase"] = "integration"
        elif blocker == "published":
            app.update("task/a", {**app.get("task/a"), "report_ref": "report/already-published"})
        elif blocker == "calls":
            monkeypatch.setattr(rt, "inference_calls_used", lambda _: config.limits.max_model_calls)
        elif blocker in {"tokens", "steps"}:
            resources = rt.resource_state(state["process_id"])
            resources["remaining_tokens" if blocker == "tokens" else "remaining_operations"] = 0
            monkeypatch.setattr(rt, "resource_state", lambda _: resources)
        else:
            monkeypatch.setattr(rt, "process_deadline", lambda _: datetime(2000, 1, 1, tzinfo=timezone.utc))
        failure = {"error": {"code": "IncompleteGeneration"}, "effects": "known",
                   "execution_termination": "confirmed_stopped", "diagnostics": {}}
        effects = rt.records.scan("effect/")
        assert not await park_model_failure(app, state, failure)
        assert not rt.records.scan("diagnosis/") and not rt.records.scan("worker-exception/")
        assert rt.records.scan("effect/") == effects
    finally:
        await rt.close()


async def test_exhausted_output_repair_enters_existing_linked_source_recovery(config):
    from test_exception_recovery import Recovering, connect, inputs, output

    from polyinference.runtime.inference import IncompleteGeneration

    class Cutoff(Recovering):
        async def generate(self, messages, *args, **kwargs):
            data = inputs(messages)
            if data.get("check_diagnosis"):
                assert data["source_previews"][0]["path"] == "a.py"
                return output({"classification": "code_failure", "guidance": "Retain the edited a.py and verify syntax"})
            if (
                data.get("assignment", {}).get("task_id") == "a"
                and data.get("phase") == "development"
                and self.counts.get(("a", "development"), 0)
            ):
                raise IncompleteGeneration(output({"partial": True}), "max_tokens", args[0])
            return await super().generate(messages, *args, **kwargs)

    config = config.model_copy(
        update={
            "model_call_retries": 0,
            "max_model_recoveries": 0,
            "inference_safety": config.inference_safety.model_copy(update={"output_recoveries": 0}),
        }
    )
    rt, app, engine = await connect(config, Cutoff(two=False))
    try:
        await engine.run()
        original = app.get("task/a")
        assert (
            original.get("exception_ref")
            and original["semantic_model_failure"]["error"]["code"] == "IncompleteGeneration"
        )
        assert not original.get("report_ref")
        packet = app.get(original["exception_ref"])
        assert packet["diagnosis"]["classification"] == "code_failure"
        diagnostic = app.get(packet["diagnosis"]["record_ref"])
        assert diagnostic["state"] == "completed"
        diagnostic_pid = "diagnostic-" + packet["diagnosis"]["record_ref"].removeprefix("diagnosis/")
        assert rt.operations.account(diagnostic_pid) == rt.operations.account(original["process_id"])
        replacements = [
            v
            for _, _, v in rt.records.scan("task/")
            if v.get("previous_process_id") == original["process_id"]
        ]
        assert len(replacements) == 1 and replacements[0]["source_delta_ref"]
        assert replacements[0]["execution"] == "completed"
        assert rt.operations.account(replacements[0]["process_id"]) == rt.operations.account(
            original["process_id"]
        )
        from datetime import datetime, timedelta

        original_deadline = rt.operations.process_deadline(original["process_id"])
        if original_deadline is None:
            original_deadline = datetime.fromisoformat(
                app.get("process/" + original["process_id"])["started_at"]
            ) + timedelta(milliseconds=config.limits.max_wall_time_ms)
        assert rt.operations.process_deadline(replacements[0]["process_id"]) == original_deadline
        from polyinference.contracts import CodeRevision

        head = CodeRevision.model_validate(app.get("head/provisional")["code"])
        assert (await rt.workspaces.tree(head.commit_id))["a.py"][1] == b"VALUE = 2\n"
        assert not rt.uncertain()
    finally:
        await rt.close()


async def test_diagnostic_reader_is_scoped_to_its_frozen_input_and_has_no_write_grants(config):
    from test_exception_recovery import connect

    rt, app, _ = await connect(config)
    try:
        app.process(
            "diag",
            app.config.check_diagnosis.role,
            entry_point="check_diagnosis",
            output_schema_ref="diagnosis/1",
        )
        raw = b"readonly source"
        rt.records.put_once(
            "diagnosis-input/diag",
            {
                "code": {"effective_tree_digest": "pinned"},
                "files": {"a.py": rt.artifacts.put(raw, app.scope("diag")).model_dump(mode="json")},
            },
        )
        state = {"process_id": "diag", "logical_step": 0}
        result, obs = await app.capability(
            state, "read", "coding.diagnostic_read", {"path": "a.py", "max_bytes": 4}, "read"
        )
        assert result.state == "succeeded" and obs["content"] == "read" and obs["returned_bytes"] == 4
        assert app.get("process/diag")["capabilities"] == ["coding.diagnostic_read"]
        result, _ = await app.capability(
            state, "foreign", "coding.diagnostic_read", {"path": "other.py"}, "read"
        )
        assert result.state == "failed"
        result, _ = await app.capability(
            state, "escape", "coding.diagnostic_read", {"path": "../escape"}, "read"
        )
        assert result.state == "failed"
        from polyinference.contracts import ArtifactRef

        assert (
            rt.artifacts.read(
                ArtifactRef.model_validate(rt.records.get("diagnosis-input/diag")[1]["files"]["a.py"])
            )
            == raw
        )
    finally:
        await rt.close()


def test_late_history_on_new_generation_does_not_resurrect_resolved_errors():
    app, state, code, histories, manifest = memory_fixture()
    histories["one"] = [error()]
    project(app, state, code)
    histories["two"] = [
        *histories["one"],
        {"id": "fixed", "reply": {"kind": "action", "tool": "files.search"}, "observation": {"matches": []}},
    ]
    state["trajectory_ref"] = "two"
    assert not project(app, state, code)["errors"]
    manifest.generation += 1
    state["trajectory_ref"] = "one"
    current = project(app, state, code)
    assert not current["errors"] and not current["files"] and current["trajectory_ref"] == "two"
    assert current["source"]["generation"] == 2


def test_resolved_historical_errors_do_not_outrank_current_work():
    from polyinference.agent.worker_memory import history_priority

    old = error()
    assert history_priority(old, {}, active_errors=set()) == 0
    assert history_priority(old, {}, active_errors={"bad"}) == 70
