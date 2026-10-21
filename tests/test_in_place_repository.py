"""Real Git behavior, separate from the historical private-copy protocol fixtures."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from types import SimpleNamespace

import pytest
from conftest import ScriptedAgent, git

from polyinference.agent.controller import ProjectAgent, tick
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig
from polyinference.contracts import CodeRevision
from polyinference.runtime.kernel import KernelRuntime


async def app_for(config, **updates):
    config = config.model_copy(update={"repository_mode": "in_place", "git_policy": {}, **updates})
    runtime = await KernelRuntime(config).open()
    scripted = ScriptedAgent()
    for name in runtime.clients:
        await runtime.clients[name].close()
        runtime.clients[name] = scripted
    app = AgentServices(runtime, config)
    return runtime, app, ProjectAgent(app), scripted


async def test_default_real_repository_merges_concurrent_workers_before_completion(config):
    runtime, app, engine, scripted = await app_for(config)
    repo = config.repo_path
    original = git(repo, "rev-parse", "HEAD")

    async def observe(data):
        if "reports" in data and data["reports"]:
            assert (repo / "a.py").read_text() == "VALUE = 2\n"
            assert (repo / "b.py").read_text() == "VALUE = 2\n"
            assert app.get("app/run")["status"] != "completed"

    scripted.hook = observe
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed", app.get("app/run")
        setup = app.get("repository/setup")
        assert not setup["isolated"]
        assert setup["original_commit"] == original
        assert git(repo, "branch", "--show-current").startswith("codex/run-")
        assert git(repo, "rev-parse", "HEAD") == app.get("head/reviewed")["code"]["commit_id"]
        assert len(runtime.records.scan("coding/worktree/")) >= 2
        for _, _, worktree in runtime.records.scan("coding/worktree/"):
            assert git(worktree["path"], "rev-parse", "--path-format=absolute", "--git-common-dir") == str(repo / ".git")
        assert git(repo, "show", original + ":a.py") == "VALUE = 1"
        assert not (config.state_path / "repository.git").exists()
        assert not runtime.records.scan("output-delivery/")
        assert app.get("coding/repository-summary")["integration_branch"] == setup["base_branch"]
        assert not runtime.records.get("coding/repository-summary-error")
        destination = config.state_path / "export.patch"
        exported = subprocess.run([sys.executable, "-m", "polyinference.cli", "export",
                                   str(config.state_path), str(destination)], capture_output=True, text=True)
        assert exported.returncode == 0, exported.stderr
        assert "+VALUE = 2" in destination.read_text()
    finally:
        await runtime.close()


async def test_no_new_branches_uses_serial_current_checkout(config):
    branch = git(config.repo_path, "branch", "--show-current")
    runtime, app, engine, scripted = await app_for(
        config, git_policy={"mode": "current", "task_branches": False, "reason": "User forbids new branches"})
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed", app.get("app/run")
        assert git(config.repo_path, "branch", "--show-current") == branch
        assert git(config.repo_path, "branch", "--format=%(refname:short)") == branch
        assert git(config.repo_path, "worktree", "list", "--porcelain").count("worktree ") == 1
        assert app.worker_limit == 1
        assert (config.repo_path / "b.py").read_text() == "VALUE = 2\n"
    finally:
        await runtime.close()


async def test_serial_policy_waits_for_active_worker_with_another_ready_task(config):
    runtime, app, engine, scripted = await app_for(
        config, git_policy={"mode": "current", "task_branches": False, "reason": "Serial project"})
    entered, release = asyncio.Event(), asyncio.Event()

    async def hold_worker(data):
        if data.get("assignment", {}).get("task_id") == "a" and data.get("phase") == "development":
            entered.set()
            await release.wait()

    scripted.hook = hold_worker
    try:
        await engine.initialize()
        await engine.review()
        await engine.dispatch()
        await asyncio.wait_for(entered.wait(), 5)
        assert app.config.max_workers == 2 and app.worker_limit == 1
        assert engine.ready() == ["task/b"]
        context = SimpleNamespace(context=SimpleNamespace(services=app))
        for _ in range(3):
            assert (await tick({}, context))["next_transition"] == "wait"
        release.set()
        await asyncio.wait_for(engine.run(), 30)
        assert app.get("app/run")["status"] == "completed"
        assert (config.repo_path / "b.py").read_text() == "VALUE = 2\n"
    finally:
        release.set()
        await runtime.close()


@pytest.mark.parametrize("mode", ["new", "existing"])
async def test_named_branch_overrides_default(config, mode):
    if mode == "existing":
        git(config.repo_path, "branch", "pi-dev")
    runtime, app, engine, _ = await app_for(config, git_policy={"mode": mode, "branch": "pi-dev"})
    try:
        await engine.initialize()
        assert git(config.repo_path, "branch", "--show-current") == "pi-dev"
        assert "codex/run-" not in git(config.repo_path, "branch", "--format=%(refname:short)")
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_dirty_checkout_is_preserved_before_policy_or_branch_mutations(config):
    (config.repo_path / "a.py").write_text("user edit\n")
    original = git(config.repo_path, "branch", "--show-current")
    runtime, app, engine, _ = await app_for(config)
    try:
        with pytest.raises(ValueError, match="Preserve existing"):
            await engine.run()
        assert (config.repo_path / "a.py").read_text() == "user edit\n"
        assert git(config.repo_path, "branch", "--show-current") == original
    finally:
        await runtime.close()


async def test_scope_violation_on_attached_directory_never_restores_or_deletes_files(config):
    runtime, app, engine, _ = await app_for(config, shell_execution="trusted")
    try:
        await engine.initialize()
        app.process("editor", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("editor", "editor", "opaque", base, ["a.py"], [])
        root = app.repository.root_for(manifest)
        result, output = await app.capability({"process_id": "editor", "workspace_id": "editor"}, "violate",
                                              "shell.run", {"script": "printf 'unauthorized' > b.py"}, "private_write")
        assert result.state == "failed"
        assert (root / "b.py").read_text() == "unauthorized"
        assert (root / "a.py").exists() and (root / ".git").exists()
        assert (config.repo_path / "b.py").read_text() == "VALUE = 1\n"
        again, _ = await app.capability({"process_id": "editor", "workspace_id": "editor"}, "again",
                                        "shell.run", {"script": "true"}, "private_write")
        assert again.state == "failed" and "blocked" in again.error.message
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_external_root_edit_blocks_integration_and_preserves_candidate(config):
    runtime, app, engine, scripted = await app_for(config)
    scripted.two = False

    async def interfere(data):
        if data.get("phase") == "assessment":
            (config.repo_path / "b.py").write_text("user concurrent edit\n")

    scripted.hook = interfere
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "paused"
        assert (config.repo_path / "b.py").read_text() == "user concurrent edit\n"
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
        assert runtime.records.scan("coding/candidate/")
    finally:
        await runtime.close()


async def test_failed_candidate_is_in_real_git_and_can_feed_a_replacement(config):
    runtime, app, engine, scripted = await app_for(config)
    scripted.two = False
    scripted.verdict = "fail"
    try:
        await engine.initialize()
        await engine.review()
        await engine.dispatch()
        await asyncio.gather(*engine.workers.values())
        await engine.consume()
        report = app.get("report/1-a")
        assert report["code_location"] == "private"
        assert git(config.repo_path, "show", report["candidate_commit_id"] + ":a.py") == "VALUE = 2"
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
        # A new worker can explicitly carry the retained candidate's scoped delta.
        app.process("replacement", "worker")
        app.update("task/replacement", {"workspace_id": "replacement", "assignment": {
            "resume_from": report["candidate_commit_id"]}})
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("replacement", "replacement", "opaque", base, ["a.py"], [])
        assert (app.repository.root_for(manifest) / "a.py").read_text() == "VALUE = 2\n"
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_interrupted_uncommitted_work_can_feed_replacement_without_unauthorized_files(config):
    runtime, app, engine, _ = await app_for(config, shell_execution="trusted")
    try:
        await engine.initialize()
        app.process("interrupted", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("interrupted", "interrupted", "opaque", base, ["a.py"], [])
        root = app.repository.root_for(manifest)
        result, _ = await app.capability({"process_id": "interrupted", "workspace_id": "interrupted"},
            "write", "shell.run", {"script": "printf 'VALUE = 9\\n' > a.py; printf ungranted > bundle.js"}, "private_write")
        assert result.state == "failed"
        assert result.extensions["polyinference/workspace-error"]["paths"] == ["bundle.js"]
        ref = await app.repository.preserve_interrupted("interrupted")
        app.process("replacement", "worker")
        app.update("task/replacement", {"workspace_id": "replacement",
            "assignment": {"resume_from": ref}})
        replacement = await app.repository.create("replacement", "replacement", "opaque", base, ["a.py"], [])
        new_root = app.repository.root_for(replacement)
        assert (new_root / "a.py").read_text() == "VALUE = 9\n"
        assert not (new_root / "bundle.js").exists()
        assert (root / "bundle.js").read_text() == "ungranted"
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
        assert git(new_root, "rev-parse", "HEAD") == base.commit_id
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_policy_model_resolves_user_instruction_before_first_write(config):
    runtime, app, engine, scripted = await app_for(config, git_policy=None,
                                                  objective="Work on this branch without creating any branches")
    original = git(config.repo_path, "branch", "--show-current")
    generate = scripted.generate

    async def policy(messages, max_output, response_schema=None):
        if any("Resolve Git instructions" in m["content"] for m in messages):
            assert git(config.repo_path, "branch", "--show-current") == original
            return {"text": json.dumps({"mode": "current", "task_branches": False,
                                        "reason": "User explicitly forbids branches"}),
                    "model": "fixture", "usage": {"total_tokens": 20}}
        return await generate(messages, max_output, response_schema)

    scripted.generate = policy
    try:
        await engine.initialize()
        assert app.get("coding/repository-policy")["task_branches"] is False
        assert git(config.repo_path, "branch", "--show-current") == original
    finally:
        await app.repository.close_run()
        await runtime.close()


def test_in_place_is_only_an_agent_default(config):
    fields = config.model_dump()
    fields.pop("repository_mode")
    assert AgentConfig.model_validate(fields).repository_mode == "in_place"
    from polyinference.config import RuntimeConfig
    assert "repository_mode" not in RuntimeConfig.model_fields


@pytest.mark.parametrize("enclosed", [False, True])
async def test_fresh_project_setup_writes_and_commits_at_requested_path(config, tmp_path, enclosed):
    parent_head = git(config.repo_path, "rev-parse", "HEAD")
    parent_branch = git(config.repo_path, "branch", "--show-current")
    repo = (config.repo_path if enclosed else tmp_path) / "fresh" / "project"
    runtime, app, engine, scripted = await app_for(config, repository=str(repo), prepare_repository=True,
                                                  allowed_write_paths=["README.md"], write_scope="project",
                                                  git_policy={"mode": "new", "branch": "pi-dev"})

    async def generate(messages, max_output, response_schema=None):
        data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                          .split("Pinned application inputs:\n", 1)[1])
        if "assignment" not in data:
            reply = {"goal": "Scaffold done", "complete": True, "dispositions": [
                {"report_ref": r["record_id"], "action": "keep", "reason": "Inspected scaffold"}
                for r in data["reports"]]}
        elif data["phase"] == "assessment":
            reply = {"kind": "assessment", "verdict": "successful", "summary": "Scaffold checked"}
        elif data["phase"] == "development" and not scripted.counts:
            if enclosed:
                assert data["repository_setup"]["startup_notes"]
                assert data["startup_notes"]
            scripted.counts["wrote"] = True
            reply = {"kind": "action", "tool": "files.write", "arguments": {
                "path": "README.md", "expected_digest": None, "content": "# Actual project\n"}}
        else:
            reply = {"kind": "candidate", "summary": "Scaffold ready"}
        return {"text": json.dumps(reply), "usage": {"total_tokens": 30}, "model": "fixture"}

    scripted.generate = generate
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed", app.get("app/run")
        assert (repo / ".git").is_dir()
        assert (repo / "README.md").read_text() == "# Actual project\n"
        assert git(repo, "show", "HEAD:README.md") == "# Actual project"
        assert git(repo, "rev-parse", "--show-toplevel") == str(repo)
        assert git(repo, "branch", "--show-current") == "pi-dev"
        assert "a.py" not in git(repo, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
        assert git(config.repo_path, "rev-parse", "HEAD") == parent_head
        assert git(config.repo_path, "branch", "--show-current") == parent_branch
    finally:
        await runtime.close()


@pytest.mark.parametrize("problem", ["collision", "missing", "invalid-policy"])
async def test_repository_setup_sends_recoverable_errors_back_to_agent(config, problem):
    if problem == "collision":
        git(config.repo_path, "branch", "pi-dev")
    initial = {"mode": "existing" if problem == "missing" else "new", "branch": "pi-dev"}
    if problem == "invalid-policy":
        initial = {"mode": "invalid"}
    runtime, app, engine, scripted = await app_for(config, git_policy=initial)
    observations = []

    async def resolve(messages, max_output, response_schema=None):
        data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                          .split("Pinned application inputs:\n", 1)[1])
        observed = data["repository_observation"]
        assert observed["setup_error"]
        assert ("pi-dev" in observed["available_branches"]) == (problem == "collision")
        observations.append(observed)
        return {"text": json.dumps({"mode": "existing" if problem == "collision" else "new",
                                    "branch": "pi-dev", "reason": "Repair observed setup failure"}),
                "model": "fixture", "usage": {"total_tokens": 20}}

    scripted.generate = resolve
    try:
        await engine.initialize()
        assert len(observations) == 1
        assert git(config.repo_path, "branch", "--show-current") == "pi-dev"
        assert app.get("repository/setup")["startup_notes"]
        assert app.get("coding/repository-policy")["reason"] == "Repair observed setup failure"
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_policy_attention_note_reaches_setup_instead_of_rejecting_start(config):
    runtime, app, engine, _ = await app_for(config, git_policy={
        "mode": "new", "blocker": "Remote publishing requires later attention"})
    try:
        await engine.initialize()
        assert app.get("app/run")["status"] == "active"
        assert "Remote publishing" in app.get("repository/setup")["startup_notes"][0]
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_failed_dependency_preparation_reaches_agent_and_can_be_retried(config):
    command = [sys.executable, "-c",
               "from pathlib import Path; assert Path('node_modules/ready').is_file(), 'prepare me'"]
    check = config.checks[0].model_copy(update={"argv": command})
    runtime, app, engine, scripted = await app_for(config, shell_execution="trusted", dependency_prepare=command,
                                                  checks=[check])
    scripted.two = False
    observed = []
    generate = scripted.generate

    async def repair(messages, max_output, response_schema=None):
        data = json.loads(next(m["content"] for m in messages if "Pinned application inputs:" in m["content"])
                          .split("Pinned application inputs:\n", 1)[1])
        if data.get("phase") == "assessment" and data["preparation_issues"]:
            assert "prepare me" in data["preparation_issues"][0]["diagnostic"]
            assert data["evidence"][0]["status"] == "failed"
            assert not app.repository.preparation_issues("unrelated-workspace")
            if observed:
                return {"text": json.dumps({"kind": "assessment", "verdict": "uncertain", "repair": True,
                                            "summary": "Prerequisites repaired; rerun checks"}),
                        "model": "fixture", "usage": {"total_tokens": 20}}
            observed.append(data["preparation_issues"])
            return {"text": json.dumps({"kind": "action", "tool": "shell.run", "arguments": {
                "script": "mkdir -p node_modules && touch node_modules/ready"}}),
                    "model": "fixture", "usage": {"total_tokens": 20}}
        return await generate(messages, max_output, response_schema)

    scripted.generate = repair
    try:
        await engine.initialize()
        await engine.review()
        await engine.dispatch()
        await asyncio.gather(*engine.workers.values())
        await engine.consume()
        assert observed
        assert app.get("task/a")["execution"] == "completed"
        assert not app.repository.preparation_issues()
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_dependency_preparation_runs_for_workers_and_independent_root_checks(config):
    marker = "from pathlib import Path; p=Path('node_modules'); p.mkdir(exist_ok=True); (p/'ready').touch()"
    check = config.checks[0].model_copy(update={"argv": [sys.executable, "-c",
        "from pathlib import Path; assert Path('node_modules/ready').is_file()"]})
    runtime, app, engine, _ = await app_for(config, shell_execution="trusted", checks=[check],
                                           dependency_prepare=[sys.executable, "-c", marker])
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "completed", app.get("app/run")
        assert (config.repo_path / "node_modules/ready").exists()
        for _, _, tree in runtime.records.scan("coding/worktree/"):
            from pathlib import Path
            assert (Path(tree["path"]) / "node_modules/ready").exists()
    finally:
        await runtime.close()


async def test_staged_worker_index_is_preserved_and_blocks_commit(config):
    runtime, app, engine, scripted = await app_for(config)
    scripted.two = False

    async def stage(data):
        if data.get("phase") == "assessment":
            manifest = app.repository.current("workspace-1-a")
            root = app.repository.root_for(manifest)
            git(root, "add", "a.py")

    scripted.hook = stage
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "paused"
        root = app.repository.root_for(app.repository.current("workspace-1-a"))
        assert git(root, "diff", "--cached", "--name-only") == "a.py"
        assert (config.repo_path / "a.py").read_text() == "VALUE = 1\n"
    finally:
        await runtime.close()


async def test_same_repository_is_excluded_across_separate_run_states(config):
    runtime, app, engine, _ = await app_for(config)
    other, second, engine2, _ = await app_for(config, state_directory=str(config.state_path) + "-second")
    other.exclusive.wait_timeout = 0.1
    try:
        await engine.initialize()
        branch = git(config.repo_path, "branch", "--show-current")
        with pytest.raises(ValueError, match="queue deadline"):
            await engine2.run()
        assert git(config.repo_path, "branch", "--show-current") == branch
    finally:
        await app.repository.close_run()
        await second.repository.close_run()
        await other.close()
        await runtime.close()


async def test_git_steering_is_applied_only_after_workers_drain(config):
    runtime, app, engine, scripted = await app_for(config)
    try:
        await engine.initialize()
        before = git(config.repo_path, "branch", "--format=%(refname:short)")
        async def resolve(messages, max_output, response_schema=None):
            return {"text": json.dumps({"mode": "current", "task_branches": False,
                                        "change_requested": True, "reason": "Latest user forbids more branches"}),
                    "model": "fixture", "usage": {"total_tokens": 20}}
        scripted.generate = resolve
        app.update("app/run", {**app.get("app/run"), "active_workers": ["still-running"]})
        denied, _ = await app.capability({"process_id": "controller"}, "too-early", "coding.reconfigure",
            {"policy": {"mode": "current", "task_branches": False}, "through": 1}, "shared_write")
        assert denied.state == "failed" and "Drain" in denied.error.message
        app.update("app/run", {**app.get("app/run"), "active_workers": []})
        update = [{"sequence": 1, "text": "Do not create any more branches. Stay here."}]
        await app.repository.apply_steering(update)
        assert app.get("coding/repository-policy")["task_branches"] is False
        assert app.worker_limit == 1
        assert git(config.repo_path, "branch", "--format=%(refname:short)") == before
        app.process("later", "worker")
        code = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("later", "later", "opaque", code, ["a.py"], [])
        assert app.repository.root_for(manifest) == config.repo_path
        assert git(config.repo_path, "branch", "--format=%(refname:short)") == before
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_attached_granted_source_takes_precedence_over_generated_output_exclusion(config):
    path = "build/source.py"
    check = config.checks[0].model_copy(update={"output_paths": ["build"]})
    runtime, app, engine, _ = await app_for(config, checks=[check], allowed_write_paths=[path])
    try:
        await engine.initialize()
        app.process("editor", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("editor", "editor", "opaque", base, [path], [])
        result, _ = await app.capability({"process_id": "editor", "workspace_id": "editor"}, "source",
            "files.write", {"path": path, "expected_digest": None, "content": "VALUE = 2\n"}, "private_write")
        assert result.state == "succeeded"
        tree = await app.repository.scan_async(app.repository.root_for(manifest))
        assert tree[path][1] == b"VALUE = 2\n"
    finally:
        await app.repository.close_run()
        await runtime.close()


async def test_native_snapshot_guard_does_not_hide_injected_git_metadata(config):
    runtime, app, engine, _ = await app_for(config)
    try:
        await engine.initialize()
        snapshot = config.state_path / "snapshots" / "guard"
        snapshot.mkdir(parents=True)
        (snapshot / ".git").write_text("unbrokered metadata")
        with pytest.raises(ValueError, match="control data"):
            await app.repository.scan_exact_async(snapshot)
        # Ordinary attached source reads still skip the actual repository metadata.
        assert ".git" not in await app.repository.scan_async(config.repo_path)
    finally:
        await app.repository.close_run()
        await runtime.close()


@pytest.mark.parametrize("failure", ["grant", "base_conflict"])
async def test_interrupted_source_rejects_reuse_without_partially_copying_edits(config, failure):
    runtime, app, engine, _ = await app_for(config)
    try:
        await engine.initialize()
        app.process("old", "worker")
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        manifest = await app.repository.create("old", "old", "opaque", base, ["a.py", "b.py"], [])
        old_root = app.repository.root_for(manifest)
        (old_root / "a.py").write_text("VALUE = 9\n")
        (old_root / "b.py").write_text("VALUE = 9\n")
        ref = await app.repository.preserve_interrupted("old")
        write_paths = ["a.py"] if failure == "grant" else ["a.py", "b.py"]
        if failure == "base_conflict":
            (config.repo_path / "b.py").write_text("VALUE = 3\n")
            git(config.repo_path, "add", "b.py")
            git(config.repo_path, "-c", "user.name=Test", "-c", "user.email=test@example.com",
                "commit", "-qm", "independent integration")
            base = base.model_copy(update={"commit_id": git(config.repo_path, "rev-parse", "HEAD")})
            app.update("head/provisional", {**app.get("head/provisional"), "code": base.model_dump(mode="json")})
        app.process("new", "worker")
        app.update("task/new", {"workspace_id": "new", "assignment": {"resume_from": ref}})
        with pytest.raises(ValueError, match="grant|conflicts"):
            await app.repository.create("new", "new", "opaque", base, write_paths, [])
        new_root = app.repository.root_for(app.repository.current("new"))
        assert (new_root / "a.py").read_text() == "VALUE = 1\n"
        assert (new_root / "b.py").read_text() == ("VALUE = 3\n" if failure == "base_conflict" else "VALUE = 1\n")
        assert (old_root / "a.py").read_text() == "VALUE = 9\n"
        assert (old_root / "b.py").read_text() == "VALUE = 9\n"
    finally:
        await app.repository.close_run()
        await runtime.close()
