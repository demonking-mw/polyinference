"""Nondefault OS settings must reach effects and survive independent state readers."""

from __future__ import annotations

import sys

import pytest
from pydantic import ValidationError

from polyinference.os_config import OSTuning
from polyinference.runtime.codex import NativeEventLog
from polyinference.runtime.commands import command
from polyinference.runtime.kernel import KernelRuntime
from polyinference.runtime.storage import Records
from polyinference.runtime.tool_environment import tool_environment
from polyinference.runtime.workspace_state import dependency_digest
from polyinference.system_settings import RuntimeConfig
from polyinference.ui_os import read_snapshot, runtime_view


def bare(tmp_path, **tuning):
    return RuntimeConfig(
        repository=str(tmp_path / "not-a-repository"),
        state_directory=str(tmp_path / "state"),
        local={"model": "fixture"},
        cloud={"model": "fixture"},
        tuning=tuning,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"events_page_size": 3, "events_page_max": 2},
        {"file_list_default": 3, "file_list_max": 2},
        {"shell_default_seconds": 61, "shell_max_seconds": 60},
        {"lock_poll_seconds": 0},
        {"native_line_bytes": 0},
        {"sqlite_timeout_seconds": float("nan")},
        {"tool_environment": {"HOME": "/user-source"}},
        {"environment_directory_names": ["../source"]},
        {"sandbox_readonly_paths": ["relative"]},
        {"unknown_knob": 1},
    ],
)
def test_invalid_tuning_rejects_before_effects(changes):
    with pytest.raises(ValidationError):
        OSTuning(**changes)


def test_grouped_settings_roundtrip_and_independent_defaults(tmp_path):
    config = RuntimeConfig.model_validate({"system": bare(tmp_path).model_dump()})
    assert config.system.tuning == config.tuning
    data = config.model_dump(mode="json")
    assert RuntimeConfig.model_validate(data) == config
    first, second = OSTuning(), OSTuning()
    with pytest.raises(TypeError, match="immutable"):
        first.tool_environment["LANG"] = "fixture"
    assert second.tool_environment["LANG"] == "C.UTF-8"
    with pytest.raises(ValidationError, match="once"):
        RuntimeConfig.model_validate({"system": data, "tuning": {}})


async def test_persisted_retention_pages_and_independent_writer(tmp_path):
    config = bare(
        tmp_path,
        journal_retention_events=3,
        events_page_size=2,
        events_page_max=2,
        sqlite_timeout_seconds=0.25,
        inspector_activity_events=1,
    )
    runtime = KernelRuntime(config)
    try:
        await runtime.open()
        other = Records(config.state_path / "records.sqlite")
        try:
            assert other.tuning == config.tuning
            assert other.db.execute("PRAGMA busy_timeout").fetchone()[0] == 250
            for index in range(5):
                other.put_once("fixture/" + str(index), {"value": index})
            assert len(other.scan("fixture/")) == 5  # Retention never removes canonical state.
            assert len(other.events()) == 2
            assert len(other.events(limit=100)) == 2
            snapshot = read_snapshot(config.state_path)
            assert len(snapshot["events"]) == 3
            view = runtime_view(snapshot, config.model_dump(mode="json"))
            assert view["journal"]["retention_limit"] == 3
            assert view["activity_page_size"] == 1
            assert len(view["activity"]) == 1
        finally:
            other.db.close()
    finally:
        await runtime.close()


async def test_unbounded_journal_and_config_pin(tmp_path):
    config = bare(tmp_path, journal_retention_events=None)
    runtime = KernelRuntime(config)
    try:
        await runtime.open()
        for index in range(20):
            runtime.records.put_once("fixture/" + str(index), {})
        assert len(read_snapshot(config.state_path)["events"]) > 20
    finally:
        await runtime.close()
    changed = config.model_copy(update={"tuning": OSTuning(journal_retention_events=2)})
    reopened = KernelRuntime(changed)
    try:
        with pytest.raises(RuntimeError, match="Configuration changed"):
            await reopened.open()
    finally:
        await reopened.close()


async def test_kernel_wires_primary_fallback_and_private_environment(tmp_path):
    config = bare(
        tmp_path,
        http_error_chars=7,
        native_event_limit=3,
        exclusive_wait_seconds=0.2,
        tool_environment={"LANG": "C", "FIXTURE_SETTING": "visible"},
    )
    data = config.model_dump()
    data["cloud"] = {
        "model": "primary",
        "protocol": "codex_app_server",
        "retry_model": {"model": "alternative"},
    }
    data["role_bindings"] = {"default": "local", "other": "cloud"}
    runtime = KernelRuntime(RuntimeConfig.model_validate(data))
    try:
        await runtime.open()
        assert runtime.exclusive.wait_timeout == 0.2
        for client in [*runtime.clients.values(), *runtime.fallback_clients.values()]:
            assert client.tuning == config.tuning
        assert runtime.clients["local"].sanitize("long diagnostic") == "long di"
        async with tool_environment(runtime.workspaces) as (env, mounts):
            assert env["LANG"] == "C" and env["FIXTURE_SETTING"] == "visible"
            assert env["HOME"].startswith(str(config.state_path))
            assert not mounts
    finally:
        await runtime.close()


def test_native_telemetry_obeys_nondefault_settings():
    log = NativeEventLog(
        10000,
        tuning=OSTuning(
            native_event_limit=2, native_recent_events=1, native_method_buckets=1, native_method_chars=4
        ),
    )
    for method in ["first", "second", "third"]:
        log.record({"method": method}, 20)
    assert len(log.snapshot()) == 2
    assert log.diagnostics()["recent_events"] == [{"method": "thir", "bytes": 20}]
    assert log.diagnostics()["methods"] == {"firs": 1, "other": 2}
    assert log.dropped_events == 1
    log.record({"method": "item/reasoning/textDelta"}, 20)
    assert len(log.snapshot()) == 2 and log.dropped_events == 2


async def test_workspace_classification_and_dependency_rules(tmp_path):
    config = bare(
        tmp_path,
        workspace_ignored_names=["scratch"],
        dependency_file_names=["deps.lock"],
        dependency_requirements_prefix="deps-",
        dependency_requirements_suffix=".list",
    )
    runtime = KernelRuntime(config)
    try:
        root = tmp_path / "view"
        (root / "scratch").mkdir(parents=True)
        (root / "scratch/source.txt").write_text("protected")
        (root / "normal.txt").write_text("source")
        view = runtime.workspaces.scan(root, (), frozenset())
        assert set(view) == {"normal.txt"}
        view = runtime.workspaces.scan(root, (), frozenset({"scratch/source.txt"}))
        assert set(view) == {"normal.txt", "scratch/source.txt"}
        other = bare(tmp_path / "other", tool_environment={"LANG": "C"})
        other_runtime = KernelRuntime(other)
        try:
            assert runtime.workspaces.environment_digest != other_runtime.workspaces.environment_digest
        finally:
            await other_runtime.close()
        before = {"deps.lock": ("100644", b"a"), "normal.txt": ("100644", b"a")}
        unrelated = {**before, "normal.txt": ("100644", b"b")}
        changed = {**before, "deps.lock": ("100644", b"b")}
        assert dependency_digest(before, config.tuning) == dependency_digest(unrelated, config.tuning)
        assert dependency_digest(before, config.tuning) != dependency_digest(changed, config.tuning)
    finally:
        await runtime.close()


async def test_small_command_chunks_preserve_combined_output_ceiling():
    argv = [sys.executable, "-c", 'import sys;sys.stdout.write("abcdef");sys.stderr.write("ghi")']
    code, out, err = await command(argv, timeout=5, output_limit=9, chunk_bytes=1)
    assert code == 0 and out == b"abcdef" and err == b"ghi"
    with pytest.raises(ValueError, match="configured limit"):
        await command(argv, timeout=5, output_limit=8, chunk_bytes=1)


async def test_file_tools_obey_pages_and_search_limits(config):
    from test_runtime import setup

    config = config.model_copy(
        update={
            "closure_paths": ["a.py", "b.py", "untouched.txt"],
            "tuning": OSTuning(
                file_list_default=1,
                file_list_max=2,
                search_matches=1,
                search_pattern_chars=5,
                search_line_chars=5,
            ),
        }
    )
    runtime, app, _ = await setup(config)
    state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
    try:
        result, page = await app.capability(state, "page-default", "files.list", {"generation": 1}, "read")
        assert result.state == "succeeded" and len(page["paths"]) == 1 and page["total"] == 3
        _, page = await app.capability(
            state, "page-large", "files.list", {"generation": 1, "limit": 100}, "read"
        )
        assert len(page["paths"]) == 2 and page["truncated"]
        _, matches = await app.capability(
            state, "search-bounded", "files.search", {"generation": 1, "pattern": "VALUE"}, "read"
        )
        assert len(matches["matches"]) == 1 and matches["truncated"]
        assert matches["matches"][0]["text"] == "VALUE"
        result, error = await app.capability(
            state, "search-long", "files.search", {"generation": 1, "pattern": "VALUE ="}, "read"
        )
        assert result.state == "failed" and "at most 5" in error["error"]
    finally:
        await runtime.close()


async def test_shell_uses_configured_default_and_ceiling(config):
    from test_runtime import setup

    config = config.model_copy(
        update={
            "shell_execution": "trusted",
            "tuning": OSTuning(shell_default_seconds=0.05, shell_max_seconds=0.1),
        }
    )
    runtime, app, _ = await setup(config)
    state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
    try:
        result, output = await app.capability(
            state, "short-default", "shell.run", {"generation": 1, "script": "sleep 1"}, "private_write"
        )
        assert result.state == "succeeded" and output["timed_out"]
        result, output = await app.capability(
            state,
            "too-long",
            "shell.run",
            {"generation": 1, "script": "true", "timeout_seconds": 1},
            "private_write",
        )
        assert result.state == "failed" and "0.1 seconds" in output["error"]
    finally:
        await runtime.close()


async def test_configured_http_pool_serializes_real_connections(tmp_path):
    import asyncio

    from polyinference.runtime.inference import HTTPInference
    from polyinference.system_settings import Endpoint

    active = peak = accepted = 0
    second_seen = asyncio.Event()

    async def handle(reader, writer):
        nonlocal active, peak, accepted
        await reader.readuntil(b"\r\n\r\n")
        active += 1
        accepted += 1
        peak = max(peak, active)
        if accepted == 2:
            second_seen.set()
        if accepted == 1:
            try:
                await asyncio.wait_for(second_seen.wait(), 0.1)
            except asyncio.TimeoutError:
                pass
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK")
        await writer.drain()
        active -= 1
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    tuning = OSTuning(http_max_connections=1, http_max_keepalive_connections=1, http_trust_environment=False)
    client = HTTPInference(
        Endpoint(model="fixture", base_url=f"http://127.0.0.1:{port}", timeout_seconds=5), tuning=tuning
    )
    try:
        responses = await asyncio.gather(
            *(client.client.get(f"http://127.0.0.1:{port}/ping") for _ in range(2))
        )
        assert all(response.text == "OK" for response in responses)
        assert accepted == 2 and peak == 1
    finally:
        await client.close()
        server.close()
        await server.wait_closed()


def test_cloud_agent_timeout_setting_is_os_owned_and_agent_visible(tmp_path):
    from polyinference.config import AgentConfig
    from polyinference.os_config import DEFAULTS

    assert DEFAULTS["RuntimeConfig"]["cloud_agent_timeout_interrupt"] is False
    base = bare(tmp_path).model_dump()
    for value in (False, True):
        data = {"objective": "fixture", "system": {**base, "allowed_write_paths": ["a.py"], "prepare_repository": True,
                "role_bindings": {"senior": "cloud", "worker": "local", "specialist": "cloud"},
                "cloud_agent_timeout_interrupt": value}}
        for cls in (RuntimeConfig, AgentConfig):
            config = cls.model_validate(data if cls is AgentConfig else {"system": data["system"]})
            assert config.cloud_agent_timeout_interrupt is value
            assert config.system.cloud_agent_timeout_interrupt is value
            assert cls.model_validate(config.model_dump()).cloud_agent_timeout_interrupt is value
            assert cls.model_json_schema()["properties"]["cloud_agent_timeout_interrupt"]["default"] is False
    for value in ("false", 0, 1, None):
        with pytest.raises(ValidationError):
            RuntimeConfig.model_validate({**base, "cloud_agent_timeout_interrupt": value})



def test_coding_presets_keep_cloud_timeout_warning_only(tmp_path):
    from polyinference.agent.system_settings import (
        coding_system_defaults,
        endpoint_profile,
        simulation_config,
        ui_system_settings,
    )
    from polyinference.config import AgentConfig

    # The coding application must inherit the OS false default, not enable interruption.
    assert "cloud_agent_timeout_interrupt" not in coding_system_defaults()
    config = AgentConfig.model_validate({**ui_system_settings(tmp_path), "objective": "fixture"})
    assert config.cloud.timeout_seconds == 1800
    assert config.cloud_agent_timeout_interrupt is False
    for profile in (None, "configured", "small-cloud", "local-inference", "buffered"):
        selected = endpoint_profile(config, profile)
        assert selected.cloud.timeout_seconds == 1800
        assert selected.cloud_agent_timeout_interrupt is False
    simulated = simulation_config(config, 2)
    assert simulated.cloud.timeout_seconds == 1800
    assert simulated.cloud_agent_timeout_interrupt is False
