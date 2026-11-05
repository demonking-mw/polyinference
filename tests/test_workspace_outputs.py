"""Build outputs, dependency continuity, and scope recovery across real views."""

from __future__ import annotations

import json
import shlex
import sys
from types import SimpleNamespace

import pytest
from conftest import git
from test_tool_environment import check_output, create_runtime

from polyinference.agent.worker import AppContext, acquire
from polyinference.contracts import ArtifactRef, CodeRevision
from polyinference.domain import Check
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.runtime.workspace_state import WriteScopeError


def build_check(script):
    return Check(name="build", argv=[sys.executable, "-c", script], output_paths=["dist"])


async def test_build_outputs_pass_and_never_enter_private_delta_or_commit(config):
    check = build_check("from pathlib import Path;p=Path('dist');p.mkdir(exist_ok=True);"
                        "(p/'index.html').write_text('built')")
    runtime, app = await create_runtime(config, [check])
    try:
        before = await runtime.workspaces.revision("fixture-ws")
        evidence = await runtime.tools.check("fixture-ws", "build")
        assert evidence["status"] == "passed", check_output(runtime, evidence)
        assert await runtime.workspaces.revision("fixture-ws") == before
        delta = app.get(await runtime.workspaces.preserve_delta("fixture-ws"))
        assert delta["changes"] == []
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        permit = await runtime.exclusive.acquire("verification/project", "fixture")
        await runtime.workspaces.integrate("fixture-ws", base, permit)
        assert (await runtime.tools.check("fixture-ws", "build"))["status"] == "passed"
        code = await runtime.workspaces.commit("fixture-ws", base, "output-test")
        assert not any(path.startswith("dist/") for path in await runtime.workspaces.tree(code.commit_id))
        await runtime.exclusive.release(permit, "fixture")
    finally:
        await runtime.close()


@pytest.mark.parametrize("path,granted", [("dist/tracked.js", False), ("dist/granted.js", True)])
async def test_output_rules_cannot_hide_tracked_or_granted_source(config, path, granted):
    if not granted:
        source = config.repo_path / path
        source.parent.mkdir()
        source.write_text("original")
        git(config.repo_path, "add", path)
        git(config.repo_path, "-c", "user.name=Test", "-c", "user.email=test@local", "commit", "-qm", "source")
    check = build_check(f"from pathlib import Path;p=Path({path!r});p.parent.mkdir(exist_ok=True);p.write_text('changed')")
    if granted:
        config = config.model_copy(update={"allowed_write_paths": [*config.allowed_write_paths, path]})
    runtime, app = await create_runtime(config, [check])
    try:
        if granted:
            base = CodeRevision.model_validate(app.get("head/provisional")["code"])
            await runtime.workspaces.create("granted-ws", "fixture", "spec", base, [path], [])
        workspace = "granted-ws" if granted else "fixture-ws"
        evidence = await runtime.tools.check(workspace, "build")
        assert evidence["status"] == "inconclusive"
        assert "Check modified source" in check_output(runtime, evidence)
        if not granted:
            with pytest.raises(WriteScopeError) as error:
                await runtime.workspaces.preserve_delta(workspace)
            assert error.value.detail["paths"] == [path]
    finally:
        await runtime.close()


async def test_shell_and_checks_share_output_policy_and_gitignore_cannot_hide_source(config):
    runtime, app = await create_runtime(config, [build_check("pass")])
    try:
        state = {"process_id": "fixture", "workspace_id": "fixture-ws"}
        script = "mkdir dist; printf built > dist/index.html"
        result, observation = await app.capability(state, "output", "shell.run", {
            "generation": 1, "script": script}, "private_write")
        assert result.state == "succeeded", observation
        assert observation["changed_paths"] == []
        root = runtime.workspaces.root_for(runtime.workspaces.current("fixture-ws"))
        (root / ".gitignore").write_text("outside.py\n")
        (root / "outside.py").write_text("hidden?")
        with pytest.raises(WriteScopeError) as error:
            await runtime.workspaces.preserve_delta("fixture-ws")
        assert "outside.py" in error.value.detail["paths"]
    finally:
        await runtime.close()


async def test_source_mutation_diagnostic_respects_output_budget(config):
    config = config.model_copy(update={"limits": config.limits.model_copy(update={"max_output_bytes": 200})})
    check = build_check("from pathlib import Path;print('x'*5000);Path('a.py').write_text('changed')")
    runtime, _ = await create_runtime(config, [check])
    try:
        evidence = await runtime.tools.check("fixture-ws", "build")
        assert evidence["status"] == "inconclusive"
        output = check_output(runtime, evidence)
        assert len(output.encode()) <= 200
        assert "Check modified source" in output and "a.py" in output
    finally:
        await runtime.close()


async def test_dependency_environment_survives_expansion_and_invalidates_on_lock_change(config):
    config = config.model_copy(update={"write_scope": "project"})
    runtime, app = await create_runtime(config, config.checks)
    try:
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await runtime.workspaces.create("env-ws", "fixture", "spec", base, ["a.py"], [], expandable=True)
        state = {"process_id": "fixture", "workspace_id": "env-ws"}
        script = ("mkdir -p node_modules/pkg node_modules/.bin; printf installed > node_modules/pkg/tool; "
                  "chmod +x node_modules/pkg/tool; ln -s ../pkg/tool node_modules/.bin/tool; "
                  "printf '{}' > package-lock.json")
        result, observation = await app.capability(state, "install", "shell.run", {
            "generation": manifest.generation, "script": script}, "private_write")
        assert result.state == "succeeded", observation
        previous = runtime.workspaces.current("env-ws")
        previous_root = runtime.workspaces.root_for(previous)
        assert (previous_root / "node_modules/pkg/tool").read_text() == "installed"
        expanded = await runtime.workspaces.extend_write_scope("env-ws", ["README.md"])
        root = runtime.workspaces.root_for(expanded)
        assert (root / "node_modules/.bin/tool").is_symlink()
        assert (root / "node_modules/pkg/tool").stat().st_mode & 0o111
        (root / "node_modules/pkg/tool").write_text("private copy")
        assert (previous_root / "node_modules/pkg/tool").read_text() == "installed"
        result, observation = await app.capability(state, "read-closure", "files.read", {
            "generation": expanded.generation, "path": "untouched.txt"})
        assert result.state == "succeeded", observation
        expanded = runtime.workspaces.current("env-ws")
        root = runtime.workspaces.root_for(expanded)
        assert (root / "node_modules/pkg/tool").read_text() == "private copy"
        await runtime.close()
        runtime = await StandaloneRuntime(runtime.config).open()
        await runtime.workspaces.prepare_environment(expanded)
        assert (root / "node_modules/pkg/tool").read_text() == "private copy"
        (root / "package-lock.json").write_text('{"changed":true}')
        await runtime.workspaces.prepare_environment(expanded)
        assert not (root / "node_modules").exists()
        assert (previous_root / "node_modules").exists()
    finally:
        await runtime.close()


async def test_tracked_dependency_directory_is_never_discarded(config):
    path = config.repo_path / "node_modules/source.py"
    path.parent.mkdir()
    path.write_text("tracked source")
    git(config.repo_path, "add", "-f", "node_modules/source.py")
    git(config.repo_path, "-c", "user.name=Test", "-c", "user.email=test@local", "commit", "-qm", "source")
    runtime, app = await create_runtime(config, config.checks)
    try:
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await runtime.workspaces.create("tracked-ws", "fixture", "spec", base,
                                                  ["a.py"], ["node_modules/source.py"])
        root = runtime.workspaces.root_for(manifest)
        await runtime.workspaces.prepare_environment(manifest)
        assert (root / "node_modules/source.py").read_text() == "tracked source"
        await runtime.close()
        runtime = await StandaloneRuntime(runtime.config).open()
        assert "node_modules/source.py" in runtime.workspaces.source_paths
        await runtime.workspaces.prepare_environment(manifest)
        assert (root / "node_modules/source.py").read_text() == "tracked source"
    finally:
        await runtime.close()


async def test_scope_failure_reaches_worker_with_paths_and_bounded_recovery(config):
    runtime, app = await create_runtime(config, config.checks)
    try:
        root = runtime.workspaces.root_for(runtime.workspaces.current("fixture-ws"))
        (root / "outside.py").write_text("retained")
        state = {"process_id": "fixture", "workspace_id": "fixture-ws", "logical_step": 0}
        context = SimpleNamespace(context=AppContext(app))
        update = await acquire(state, context)
        assert update["route"] == "model" and update["scope_recoveries"] == 1
        history = json.loads(runtime.artifacts.read(ArtifactRef.model_validate(update["trajectory_ref"])))
        assert "outside.py" in json.dumps(history)
        assert (root / "outside.py").read_text() == "retained"
        assert not runtime.records.get("permit/verification/project")
        update = await acquire({**state, "scope_recoveries": config.limits.max_repairs}, context)
        assert update["route"] == "park"
        (root / "outside.py").unlink()
        recovered = await acquire({**state, **update}, context)
        assert recovered["route"] == "integrate" and recovered["interrupted"] is None
        await runtime.exclusive.release(recovered["verification_permit_ref"], "fixture")
    finally:
        await runtime.close()


async def test_setup_declares_and_persists_output_policy(config):
    check = build_check("from pathlib import Path;p=Path('dist');p.mkdir(exist_ok=True);"
                        "(p/'index.html').write_text('built')")
    runtime, app = await create_runtime(config, [])
    try:
        app.update("task/project_setup", {"workspace_id": "fixture-ws"})
        request = SimpleNamespace(payload=SimpleNamespace(workspace_id="fixture-ws"))
        selected = await app.runtime_policy.configure_checks(request, check.model_dump(mode="json"))
        assert selected["checks"][0]["output_paths"] == ["dist"]
        assert (await runtime.tools.check("fixture-ws", "build"))["status"] == "passed"
        with pytest.raises(ValueError, match="overlap"):
            await app.runtime_policy.configure_checks(request, {**check.model_dump(), "output_paths": ["a.py"]})
        await runtime.close()
        runtime = await StandaloneRuntime(runtime.config).open()
        assert runtime.tools.check_definitions()[0].output_paths == ["dist"]
        assert (await runtime.tools.check("fixture-ws", "build"))["status"] == "passed"
    finally:
        await runtime.close()


async def test_dependency_runtime_can_execute_after_scope_expansion(config):
    config = config.model_copy(update={"write_scope": "project"})
    script = "from pathlib import Path;assert Path('node_modules/installed').read_text()=='yes'"
    runtime, app = await create_runtime(config, [Check(name="installed", argv=[sys.executable, "-c", script])])
    try:
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        await runtime.workspaces.create("env-ws", "fixture", "spec", base, ["a.py"], [], expandable=True)
        install = "from pathlib import Path;p=Path('node_modules');p.mkdir();(p/'installed').write_text('yes')"
        result, obs = await app.capability({"process_id": "fixture", "workspace_id": "env-ws"},
            "install", "shell.run", {"generation": 1, "script": shlex.join([sys.executable, "-c", install])},
            "private_write")
        assert result.state == "succeeded", obs
        await runtime.workspaces.extend_write_scope("env-ws", ["README.md"])
        assert (await runtime.tools.check("env-ws", "installed"))["status"] == "passed"
    finally:
        await runtime.close()
