"""Tool housekeeping must not become assessed or published source changes."""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import sys
from pathlib import Path

import pytest

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.services import AgentServices
from polyinference.contracts import ArtifactRef, CodeRevision
from polyinference.domain import Check
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.runtime.tool_environment import tool_environment

WRITE_HOUSEKEEPING = """import json,os
from pathlib import Path
names=['HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_STATE_HOME',
       'TMPDIR','TMP','TEMP','npm_config_cache','PIP_CACHE_DIR']
locations={name:os.environ[name] for name in names}
for value in locations.values():
 p=Path(value);p.mkdir(parents=True,exist_ok=True);(p/'housekeeping').write_text('cache')
log=Path(locations['HOME'])/'.npm'/'_logs'/'test.log'
log.parent.mkdir(parents=True,exist_ok=True);log.write_text('npm log')
print(json.dumps(locations),flush=True)
"""


def check_output(runtime, evidence):
    return runtime.artifacts.read(ArtifactRef.model_validate(evidence["output"])).decode()


def native_npm_command():
    # A WSL PATH can also contain Windows npm wrappers that run node.exe.
    for directory in os.get_exec_path():
        node, npm = Path(directory) / "node", Path(directory) / "npm"
        if node.is_file() and npm.is_file():
            return [str(node), str(npm.resolve()), "test"]
    return None


async def create_runtime(config, checks):
    config = config.model_copy(update={"checks": checks, "shell_execution": "trusted"})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    await ProjectAgent(app).initialize()
    app.process("fixture", "worker")
    base = CodeRevision.model_validate(app.get("head/provisional")["code"])
    await runtime.workspaces.create("fixture-ws", "fixture", "fixture-spec", base, ["a.py"], ["a.py"])
    return runtime, app


@pytest.mark.parametrize("outcome", ["passed", "failed", "timeout", "unavailable"])
async def test_check_housekeeping_is_isolated_and_cleaned(config, outcome):
    script = WRITE_HOUSEKEEPING
    if outcome == "failed":
        script += "raise SystemExit(7)\n"
    elif outcome == "timeout":
        script += "import time;time.sleep(60)\n"
    argv = [sys.executable, "-c", script] if outcome != "unavailable" else ["/missing/check-executable"]
    check = Check(name="housekeeping", argv=argv, timeout_seconds=0.5 if outcome == "timeout" else 10)
    runtime, app = await create_runtime(config, [check])
    try:
        before = await runtime.workspaces.revision("fixture-ws")
        evidence = await runtime.tools.check("fixture-ws", check.name)
        expected = "inconclusive" if outcome == "timeout" else outcome
        assert evidence["status"] == expected
        assert await runtime.workspaces.revision("fixture-ws") == before
        assert "Check modified source" not in check_output(runtime, evidence)
        if outcome in {"passed", "failed"}:
            locations = json.loads(check_output(runtime, evidence))
            for value in locations.values():
                assert Path(value).is_relative_to(config.state_path)
                assert not Path(value).is_relative_to(runtime.workspaces.root)
                assert not Path(value).exists()
        assert not list(config.state_path.glob("tool-environment-*"))
        assert runtime.records.get("permit/shell/installation")[1]["process_id"] is None
        delta = await runtime.workspaces.preserve_delta("fixture-ws")
        assert app.get(delta)["changes"] == []
    finally:
        await runtime.close()


@pytest.mark.skipif(native_npm_command() is None, reason="Native Node/npm is needed to reproduce npm housekeeping")
async def test_failed_npm_test_does_not_create_out_of_scope_source(config):
    # WSL may put Windows npm/node ahead of Linux tools on PATH. Pin the Linux
    # interpreter and CLI so this exercises the supported POSIX environment.
    check = Check(name="npm-missing-manifest", argv=native_npm_command(), timeout_seconds=30)
    runtime, app = await create_runtime(config, [check])
    try:
        evidence = await runtime.tools.check("fixture-ws", check.name)
        assert evidence["status"] == "failed" and evidence["exit_code"] != 0
        assert "package.json" in check_output(runtime, evidence)
        root = runtime.workspaces.root_for(runtime.workspaces.current("fixture-ws"))
        assert not (root / ".npm").exists()
        assert not list(config.state_path.glob("tool-environment-*"))
        delta = await runtime.workspaces.preserve_delta("fixture-ws")
        assert app.get(delta)["changes"] == []
    finally:
        await runtime.close()


async def test_shell_housekeeping_does_not_expand_write_scope(config):
    runtime, app = await create_runtime(config, config.checks)
    try:
        manifest = runtime.workspaces.current("fixture-ws")
        state = {"process_id": "fixture", "workspace_id": "fixture-ws", "logical_step": 0}
        result, observation = await app.capability(state, "shell-cache", "shell.run", {
            "generation": manifest.generation,
            "script": shlex.join([sys.executable, "-c", WRITE_HOUSEKEEPING]),
        }, "private_write")
        assert result.state == "succeeded" and observation["exit_code"] == 0
        assert observation["changed"] is False and observation["changed_paths"] == []
        assert runtime.workspaces.current("fixture-ws").allowed_write_paths == ["a.py"]
        assert not list(config.state_path.glob("tool-environment-*"))
        assert runtime.records.get("permit/shell/installation")[1]["process_id"] is None
    finally:
        await runtime.close()


async def test_cancelled_check_cleans_tool_home_and_releases_lease(config):
    check = Check(name="cancel", argv=[sys.executable, "-c", WRITE_HOUSEKEEPING + "import time;time.sleep(60)"])
    runtime, _ = await create_runtime(config, [check])
    task = asyncio.create_task(runtime.tools.check("fixture-ws", check.name))

    async def started():
        while not list(config.state_path.glob("tool-environment-*/home/housekeeping")):
            await asyncio.sleep(0.01)

    try:
        await asyncio.wait_for(started(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not list(config.state_path.glob("tool-environment-*"))
        assert runtime.records.get("permit/shell/installation")[1]["process_id"] is None
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await runtime.close()


async def test_cache_named_source_changes_still_invalidate_evidence_and_fail_scope(config):
    script = "from pathlib import Path;p=Path('.npm');p.mkdir();(p/'source.js').write_text('unauthorized')"
    check = Check(name="mutating", argv=[sys.executable, "-c", script])
    runtime, app = await create_runtime(config, [check])
    try:
        evidence = await runtime.tools.check("fixture-ws", check.name)
        assert evidence["status"] == "inconclusive"
        assert "Check modified source" in check_output(runtime, evidence)
        with pytest.raises(ValueError, match="Private changes exceed write scope"):
            await runtime.workspaces.preserve_delta("fixture-ws")
    finally:
        await runtime.close()


async def test_sandbox_environment_uses_an_explicit_separate_mount(config):
    runtime, _ = await create_runtime(config, config.checks)
    try:
        async with tool_environment(runtime.workspaces, sandboxed=True) as (environment, mounts):
            assert mounts[0] == "--bind" and mounts[2] == "/tool-environment"
            host = Path(mounts[1])
            assert host.is_dir() and not host.is_relative_to(runtime.workspaces.root)
            for name in ["HOME", "XDG_CACHE_HOME", "TMPDIR", "npm_config_cache"]:
                visible = Path(environment[name])
                assert visible.is_relative_to(Path("/tool-environment"))
                assert (host / visible.relative_to("/tool-environment")).is_dir()
        assert not host.exists()
    finally:
        await runtime.close()
