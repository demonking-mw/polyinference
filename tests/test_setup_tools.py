from __future__ import annotations

import asyncio
import json
import shlex
import threading
from pathlib import Path

import httpx
import pytest
from conftest import ScriptedAgent, fixture_completion, fixture_review_reply, git

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.routing import accounting, allocate
from polyinference.agent.services import AgentServices
from polyinference.config import AgentConfig
from polyinference.contracts import CodeRevision, TaskSpec
from polyinference.domain import Assignment
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.ui import TestUI, make_server


def pinned(messages):
    return json.loads(
        next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
            "Pinned application inputs:\n", 1
        )[1]
    )


@pytest.mark.parametrize("automatic_checks", [False, True])
async def test_cloud_setup_selects_requested_branch_runs_shell_and_publishes_before_planning(config, automatic_checks):
    source = Path(config.repository)
    original = git(source, "branch", "--show-current")
    git(source, "checkout", "-qb", "requested-base")
    (source / "branch.txt").write_text("selected branch\n")
    git(source, "add", ".")
    git(source, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-qm", "branch")
    branch_commit = git(source, "rev-parse", "HEAD")
    git(source, "checkout", original)
    config = config.model_copy(
        update={
            "prepare_repository": True,
            "write_scope": "project",
            "shell_execution": "trusted",
            "objective": "Use requested-base as main, write setup.txt, then update a.py",
            "cloud": config.cloud.model_copy(update={"protocol": "codex_app_server", "brokered_tools": True}),
        }
    )
    original_checks = config.checks
    if automatic_checks:
        config = config.model_copy(update={"checks": []})
    junior = ScriptedAgent(two=False)
    called = []
    runtime = await StandaloneRuntime(config).open()

    class Cloud:
        async def generate_job(self, messages, snapshot, schema, callback=None):
            data = pinned(messages)
            called.append(data)
            if "assignment" in data:
                assert data["assignment"]["task_id"] == "project_setup"
                assert "first cloud engineer" in messages[0]["content"]
                if data["phase"] == "development":
                    assert "requested-base" in data["repository_setup"]["branches"]
                    selected = await callback(
                        "select-base",
                        {"tool": "repository.select_branch", "arguments": {"name": "requested-base"}},
                    )
                    assert selected["state"] == "succeeded", selected
                    if automatic_checks:
                        check = {**original_checks[0].model_dump(mode="json"), "purpose": "acceptance"}
                        observation = await callback("choose-check", {"tool": "checks.configure", "arguments": check})
                        assert observation["state"] == "succeeded", observation
                        replay = await callback("choose-check", {"tool": "checks.configure", "arguments": check})
                        assert replay == observation
                        replacement = await callback("replace-check", {
                            "tool": "checks.configure", "arguments": {**check, "argv": ["replacement"]},
                        })
                        assert replacement["state"] == "failed", replacement
                        # Native jobs may run the selected check before returning to application code.
                        observation = await callback("run-selected", {
                            "tool": "checks.run", "arguments": {"name": check["name"]},
                        })
                        assert observation["observation"]["status"] == "passed", observation
                    observation = await callback(
                        "setup-script",
                        {
                            "tool": "shell.run",
                            "arguments": {
                                "script": "printf 'prepared\\n' > setup.txt; printf 'done'",
                                "timeout_seconds": 5,
                            },
                        },
                    )
                    assert observation["state"] == "succeeded", observation
                    assert observation["observation"]["stdout"] == "done"
                    # A duplicated callback returns its durable observation without rerunning the script.
                    replay = await callback(
                        "setup-script",
                        {
                            "tool": "shell.run",
                            "arguments": {
                                "script": "printf 'prepared\\n' > setup.txt; printf 'done'",
                                "timeout_seconds": 5,
                            },
                        },
                    )
                    assert replay == observation
                reply = (
                    {"kind": "assessment", "verdict": "successful", "summary": "Setup verified"}
                    if data["phase"] == "assessment"
                    else {"kind": "candidate", "summary": "Ready"}
                )
            else:
                assert runtime.records.get("setup/completed")
                assert data["repository_setup"]["base_branch"] == "requested-base"
                assert data["write_scope"] == "project"
                reply = {
                    "goal": "Update value",
                    "dispositions": [
                        {"report_ref": r["record_id"], "action": "keep", "reason": "Inspected"}
                        for r in data["reports"]
                    ],
                }
                if "a" not in data["all_task_ids"]:
                    reply["tasks"] = [
                        {
                            "task_id": "a",
                            "objective": "Update a.py",
                            "write_paths": ["a.py"],
                            "read_paths": ["a.py"],
                            "checks": ["syntax"],
                        }
                    ]
                else:
                    reply["complete"] = True
                    reply["completion_assessment"] = fixture_completion(data)
            return {
                "text": json.dumps(fixture_review_reply(reply, data)),
                "model": "cloud-fixture",
                "usage": {"total_tokens": 50},
                "events": [],
            }

        async def close(self):
            pass

    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": junior, "cloud": Cloud()}
    app = AgentServices(runtime, config)
    try:
        outcome = await ProjectAgent(app).run()
        assert outcome["outcome"] == "completed", app.get("app/run")
        assert "assignment" in called[0]
        assert app.get("head/initial")["code"]["commit_id"] == branch_commit
        final = await runtime.workspaces.tree(app.get("head/provisional")["code"]["commit_id"])
        assert final["branch.txt"][1] == b"selected branch\n"
        assert final["setup.txt"][1] == b"prepared\n"
        assert final["a.py"][1] == b"VALUE = 2\n"
        assert app.get("task/project_setup")["category"] == "setup"
        assert app.get(app.get("task/project_setup")["plan_ref"])["kind"] == "sprint_plan"
        assert app.get("task/a")["assignment"]["role"] == "worker"
        setup = app.get(app.get("task/project_setup")["report_ref"])
        assert setup["original_base"]["commit_id"] == branch_commit
        assert TaskSpec.model_validate(app.get(setup["task_spec_ref"])).base.commit_id == branch_commit
        children = [e for _, _, e in runtime.records.scan("effect/") if e["request"].get("causal_parent_ref")]
        assert len(children) == (5 if automatic_checks else 2)
        assert git(source, "branch", "--show-current") == original
        assert not (source / "setup.txt").exists()
        assert git(source, "status", "--porcelain") == ""
    finally:
        await runtime.close()
    if automatic_checks:
        reopened = await StandaloneRuntime(config).open()
        try:
            assert AgentServices(reopened, config).check_definitions == original_checks
            assert reopened.records.get("setup/checks")[1]["checks"] == [c.model_dump(mode="json") for c in original_checks]
        finally:
            await reopened.close()


@pytest.mark.parametrize("project_kind", ["populated", "empty", "missing"])
async def test_prepare_initializes_private_git_for_plain_folder_without_tracking_secrets(
    config, tmp_path, project_kind
):
    source = tmp_path / "new-project" / "nested"
    empty = project_kind != "populated"
    if project_kind != "missing":
        source.mkdir(parents=True)
    if source.exists():
        (source / ".npm" / "_logs").mkdir(parents=True)
        (source / ".npm" / "_logs" / "cached.log").write_text("generated npm log\n")
    if not empty:
        (source / "main.py").write_text("VALUE = 1\n")
        (source / ".env").write_text("SECRET=fixture\n")
        (source / ".gitignore").write_text("ignored.txt\n")
        (source / "ignored.txt").write_text("ignored\n")
    selected = config.model_copy(
        update={"repository": str(source), "prepare_repository": True, "write_scope": "project"}
    )
    runtime = await StandaloneRuntime(selected).open()
    try:
        code = await runtime.workspaces.initialize()
        assert source.is_dir()
        tree = await runtime.workspaces.tree(code.commit_id)
        assert ".env" not in tree and "ignored.txt" not in tree
        assert not any(path.startswith(".npm/") for path in tree)
        assert ("main.py" in tree) != empty
        assert not (source / ".git").exists()
        assert runtime.records.get("repository/setup")[1]["base_branch"] == "main"
        repeated = await runtime.workspaces.initialize()
        assert repeated == code
        if empty:
            from polyinference.agent.tasks import make_task

            app = AgentServices(runtime, selected)
            assignment = Assignment(
                task_id="empty-setup", objective="Prepare", write_paths=["README.md"], checks=["syntax"]
            )
            task, specs = make_task(
                app, assignment, "setup-test", code.model_dump(mode="json"), "empty-setup", "setup"
            )
            runtime.records.compare_and_publish({}, {}, specs)
            app.process(task["process_id"], assignment.role, task["spec_ref"], task)
            await runtime.workspaces.create(
                task["workspace_id"], task["process_id"], task["spec_ref"], code, ["README.md"], sorted(tree)
            )
            await runtime.workspaces.select_branch(task["workspace_id"], "new-project", create=True)
            assert "README.md" in runtime.workspaces.current(task["workspace_id"]).allowed_write_paths
            assert runtime.workspaces.current(task["workspace_id"]).copied_files
    finally:
        await runtime.close()


def test_development_allocation_is_cumulative_and_excludes_setup_and_management():
    def task(name, role="worker"):
        return Assignment(
            task_id=name, objective=name, write_paths=[name + ".py"], checks=["syntax"], role=role
        )

    retained = [{"category": "setup", "execution": "completed", "assignment": {"role": "specialist"}}]
    roles = []
    for batch in range(4):
        proposed = [task(f"t{batch}_{i}", "specialist" if i == 2 else "worker") for i in range(5)]
        assigned = allocate(proposed, retained, 0.1)
        roles.extend(t.role for t in assigned)
        retained.extend(
            {"category": "development", "execution": "completed", "assignment": t.model_dump()}
            for t in assigned
        )
    assert roles.count("specialist") == 2 and roles.count("worker") == 18
    assert roles[:5].count("specialist") == 1
    assert roles[2] == "specialist"  # Prefer the senior's nominated complex task.
    assert all(t.role == "worker" for t in allocate([task("off", "specialist")], [], 0))
    assert all(t.role == "specialist" for t in allocate([task("on")], [], 1))


@pytest.mark.parametrize("start_evidence", [{"started_at": "2026-10-21T13:00:00+00:00"},
                                           {"spec_ref": "task-spec/old:started"}])
def test_cancelled_started_tasks_remain_in_accounting_and_role_history(start_evidence):
    task = {"category": "development", "execution": "cancelled",
            "assignment": {"role": "specialist"}, **start_evidence}
    pending_cancel = {"category": "development", "execution": "cancelled",
                      "assignment": {"role": "worker"}}
    records = {"task/started": task, "task/unstarted": pending_cancel}
    result = accounting(records, 0.5)
    assert result["started_development_tasks"] == result["senior_tasks"] == 1
    assert result["junior_tasks"] == 0
    proposed = Assignment(task_id="next", objective="Next", write_paths=["a.py"], checks=["syntax"])
    assert allocate([proposed], list(records.values()), 0.5)[0].role == "worker"
    # Pending assignments reserve quota but never inflate the reported start count.
    records["task/reserved"] = {"category": "development", "execution": "pending",
                                 "assignment": {"role": "worker"}}
    assert accounting(records)["started_development_tasks"] == 1
    assert allocate([proposed], list(records.values()), 0.5)[0].role == "specialist"


async def test_retiring_started_development_preserves_count_and_replacement_allocation(config):
    config = config.model_copy(update={"senior_development_fraction": 0.5})

    class RetiringAgent(ScriptedAgent):
        async def generate(self, messages, *args):
            data = pinned(messages)
            if data.get("assignment", {}).get("task_id") == "a":
                from polyinference.runtime.inference import ProviderError

                raise ProviderError("Fixture known-stopped failure", category="invalid_request", submitted=False)
            elif "assignment" not in data and data["all_task_ids"] and "b" not in data["all_task_ids"]:
                reply = {"goal": "Replace a", "cancel_pending_task_ids": ["a"], "tasks": [{
                    "task_id": "b", "objective": "Set b to 2", "write_paths": ["b.py"],
                    "read_paths": ["b.py"], "checks": ["syntax"]}]}
            else:
                return await super().generate(messages, *args)
            return {"text": json.dumps(fixture_review_reply(reply, data)), "model": "fixture", "usage": {"total_tokens": 5}}

    runtime = await StandaloneRuntime(config).open()
    client = RetiringAgent(two=False)
    for old in runtime.clients.values():
        await old.close()
    runtime.clients = {name: client for name in runtime.clients}
    app, engine = AgentServices(runtime, config), None
    engine = ProjectAgent(app)
    try:
        await engine.run()
        assert app.get("app/run")["status"] == "paused"
        engine.steer("Retire the safely stopped assignment a and replace it with b")
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        assert app.get("task/a")["execution"] == "cancelled"
        assert app.get("task/a")["started_at"]
        assert app.get("task/b")["assignment"]["role"] == "worker"
        records = {key: body for key, _, body in runtime.records.scan("task/")}
        assert accounting(records)["started_development_tasks"] == 2
        assert accounting(records)["senior_tasks"] == 1
        await engine.run()
        assert accounting({key: body for key, _, body in runtime.records.scan("task/")}) == accounting(records)
    finally:
        await runtime.close()


async def test_setup_discovered_task_check_is_not_implicitly_final_acceptance(config):
    config = config.model_copy(update={"checks": [], "prepare_repository": True})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.initialize()
        from polyinference.domain import Check
        check = Check(name="environment", argv=["true"])
        runtime.tools.register_check(check)
        app.update("setup/checks", {"checks": [check.model_dump(mode="json")]})
        assert not await engine.accept()
        assert not runtime.records.scan("acceptance-receipt/")
        assert not runtime.records.scan("output-delivery/")
    finally:
        await runtime.close()


async def test_initial_check_discovery_pins_purposes_without_promoting_prerequisites(config):
    config = config.model_copy(update={"checks": [], "prepare_repository": True})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    try:
        await ProjectAgent(app).initialize()
        app.process("selector", "specialist", task_data={
            "category": "setup", "attempt_id": "selector", "workspace_id": "selection"})
        base = CodeRevision.model_validate(app.get("head/provisional")["code"])
        await runtime.workspaces.create("selection", "selector", "opaque", base, ["a.py"], ["a.py"],
                                        capabilities=["checks.configure"], check_names=[])
        app.update("task/project_setup", {"workspace_id": "selection"})
        state = {"process_id": "selector", "workspace_id": "selection", "logical_step": 0}
        for purpose in ("prerequisite", "task", "acceptance"):
            result, _ = await app.capability(state, "select-" + purpose, "checks.configure", {
                "name": purpose, "argv": ["true"], "purpose": purpose}, "private_write")
            assert result.state == "succeeded"
            if purpose == "prerequisite":
                assert not app.task_check_definitions and not app.acceptance_check_definitions
        assert [c.name for c in app.setup_check_definitions] == ["prerequisite"]
        assert {c.name for c in app.task_check_definitions} == {"task", "acceptance"}
        assert [c.name for c in app.acceptance_check_definitions] == ["acceptance"]
        result, _ = await app.capability(state, "weaken", "checks.configure", {
            "name": "weaker", "argv": ["true"], "purpose": "acceptance"}, "private_write")
        assert result.state == "failed"
        app.update("setup/completed", {"process_id": "selector"})
        result, _ = await app.capability(state, "late", "checks.configure", {
            "name": "late", "argv": ["true"], "purpose": "task"}, "private_write")
        assert result.state == "failed"
    finally:
        await runtime.close()


async def test_explicit_product_acceptance_is_distinct_from_prerequisite_and_task_checks(config):
    prerequisite = config.checks[0].model_copy(update={"name": "environment", "argv": ["true"]})
    product = config.checks[0].model_copy(update={"name": "product", "argv": [
        "python3", "-c", "import pathlib; assert pathlib.Path('a.py').read_text() == 'VALUE = 2\\n'"]})
    config = config.model_copy(update={"prerequisite_checks": [prerequisite], "acceptance_checks": [product]})
    runtime = await StandaloneRuntime(config).open()
    client = ScriptedAgent(two=False)
    for old in runtime.clients.values():
        await old.close()
    runtime.clients = {name: client for name in runtime.clients}
    app = AgentServices(runtime, config)
    engine = ProjectAgent(app)
    try:
        await engine.initialize()
        assert not await engine.accept()  # Environment and syntax pass, requested behavior does not.
        assert not runtime.records.scan("acceptance-receipt/")
        await engine.run()
        assert app.get("app/run")["status"] == "completed"
        receipt = app.get(app.get("app/run")["acceptance_ref"])
        assert [e["criterion_ref"] for e in receipt["evidence"]] == ["product"]
    finally:
        await runtime.close()


@pytest.mark.parametrize("exists", [False, True])
async def test_ui_accepts_plain_project_folder_and_preserves_explicit_branch(config, tmp_path, exists):
    source = tmp_path / "plain" / "nested"
    if exists:
        source.mkdir(parents=True)
    manager = TestUI(tmp_path / "ui")
    options = manager.repository_options(str(source))
    assert options["repository"] == str(source) and options["file_count"] == 0
    selected = manager.configure_run(str(source), "python3 -m unittest")
    assert selected.prepare_repository and selected.write_scope == "project"
    assert selected.role_bindings["specialist"] == "cloud"
    assert selected.shell_execution == "trusted"
    assert selected.cloud.brokered_tools
    assert source.exists() == exists  # Selection/preview must not create the project.


@pytest.mark.parametrize("automatic_checks", [False, True])
@pytest.mark.parametrize("launch", ["direct", "ui"])
async def test_default_setup_creates_missing_project_and_follows_objective_before_planning(config, tmp_path, launch, automatic_checks):
    source = tmp_path / "new-parent" / "project"
    selected = AgentConfig.model_validate({
        **config.model_dump(exclude={"prepare_repository"}),
        "repository": str(source),
        "objective": "Prepare src/ready.py with READY = True before planning.",
        "write_scope": "project",
    })
    assert selected.prepare_repository
    import sys

    command = [sys.executable, "-c", "from pathlib import Path; assert Path('src/ready.py').read_text() == 'READY = True\\n'"]
    if automatic_checks:
        selected = selected.model_copy(update={
            "checks": [], "objective": selected.objective + " Verify with: " + shlex.join(command),
        })
    runtime = None
    calls = []

    class Cloud:
        async def generate(self, messages, max_output, response_schema=None):
            data = pinned(messages)
            calls.append(data)
            if "assignment" in data:
                assert data["assignment"]["task_id"] == "project_setup"
                assert data["user_objective"] == selected.objective
                assert data["repository_setup"]["source_repository"] == str(source)
                assert data["repository_setup"]["git_initialized"]
                assert source.is_dir()
                assert (runtime.config.state_path / "repository.git").is_dir()
                if data["phase"] == "development" and len(calls) == 1:
                    reply = {
                        "kind": "action", "tool": "files.write",
                        "arguments": {
                            "path": "src/ready.py", "expected_digest": None, "content": "READY = True\n",
                        },
                    }
                elif automatic_checks and data["phase"] == "development" and not data["configured_checks"]:
                    assert shlex.join(command) in data["user_objective"]
                    assert "checks.configure" in data["available_tools"]
                    reply = {"kind": "action", "tool": "checks.configure", "arguments": {
                        "name": "ready", "argv": command, "purpose": "acceptance",
                    }}
                elif data["phase"] == "assessment":
                    if automatic_checks:
                        assert data["assignment"]["checks"] == ["ready"]
                        assert data["evidence"][0]["status"] == "passed"
                    reply = {"kind": "assessment", "verdict": "successful", "summary": "Setup checked"}
                else:
                    reply = {"kind": "candidate", "summary": "Ready for planning"}
            else:
                assert runtime.records.get("setup/completed")
                code = runtime.records.get("head/provisional")[1]["code"]
                tree = await runtime.workspaces.tree(code["commit_id"])
                assert tree["src/ready.py"][1] == b"READY = True\n"
                reply = {
                    "goal": "Requested setup complete", "complete": True,
                    "dispositions": [
                        {"report_ref": report["record_id"], "action": "keep", "reason": "Reviewed"}
                        for report in data["reports"]
                    ],
                }
            return {"text": json.dumps(fixture_review_reply(reply, data)), "model": "cloud-fixture", "usage": {"total_tokens": 50}}

        async def close(self):
            pass

    async def run(run_config):
        nonlocal runtime
        runtime = await StandaloneRuntime(run_config).open()
        try:
            for client in runtime.clients.values():
                await client.close()
            runtime.clients = {"local": ScriptedAgent(two=False), "cloud": Cloud()}
            app = AgentServices(runtime, run_config)
            engine = ProjectAgent(app)
            outcome = await engine.run()
            assert outcome["outcome"] == "completed", app.get("app/run")
            assert calls[0]["assignment"]["task_id"] == "project_setup"
            assert runtime.records.get("setup/completed")
            count = len(calls)
            await engine.run()
            assert len(calls) == count  # Completed setup is retained when execution resumes.
            return outcome
        finally:
            await runtime.close()

    if launch == "direct":
        await run(selected)
        return

    path = tmp_path / "config.json"
    path.write_text(selected.model_dump_json())
    manager = TestUI(tmp_path / "ui", config_path=path, runner=run)
    server = make_server(manager, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    try:
        async with httpx.AsyncClient(base_url=origin, headers={"Origin": origin}) as client:
            page = (await client.get("/")).text
            assert "Project path" in page and "Use this folder" in page
            preview = await client.get("/api/repository", params={"path": str(source)})
            assert preview.status_code == 200 and preview.json()["file_count"] == 0
            picker = (await client.get("/api/directories", params={"path": str(source)})).json()
            assert picker["is_repository"] and not picker["exists"]
            assert not source.exists()
            response = await client.post("/api/run", json={
                "repository": str(source), "objective": selected.objective,
                "check_command": "" if automatic_checks else shlex.join(selected.checks[0].argv),
            })
            assert response.status_code == 202, response.text
            run_id = response.json()["id"]
            for _ in range(500):
                view = (await client.get("/api/run", params={"id": run_id})).json()
                if view["status"] != "running":
                    break
                await asyncio.sleep(0.02)
            assert view["status"] == "completed", view
            assert source.is_dir()
            snapshots = list((tmp_path / "history").glob("*.json"))
            assert len(snapshots) == 1
            assert json.loads(snapshots[0].read_text())["run"]["id"] == run_id
    finally:
        await asyncio.to_thread(server.shutdown)
        server.server_close()
        thread.join(timeout=2)


async def test_project_setup_rejects_file_paths_and_respects_explicit_opt_out(config, tmp_path):
    from polyinference.ui_repository import project

    source = tmp_path / "file.txt"
    source.write_text("Keep this file")
    with pytest.raises(ValueError, match="must be a directory"):
        project(str(source))
    selected = config.model_copy(update={"repository": str(source), "prepare_repository": True})
    runtime = await StandaloneRuntime(selected).open()
    try:
        with pytest.raises(ValueError, match="must be a directory"):
            await runtime.workspaces.initialize()
        assert source.read_text() == "Keep this file"
        assert not runtime.workspaces.gitdir.exists()
        missing = tmp_path / "missing"
        runtime.workspaces.config = selected.model_copy(
            update={"repository": str(missing), "prepare_repository": False}
        )
        with pytest.raises(ValueError, match="enable prepare_repository"):
            await runtime.workspaces.initialize()
        assert not missing.exists()
    finally:
        await runtime.close()


async def test_explicit_base_branch_is_selected_without_changing_source_checkout(config):
    source = Path(config.repository)
    original = git(source, "branch", "--show-current")
    git(source, "branch", "feature")
    selected = config.model_copy(update={"base_branch": "feature"})
    runtime = await StandaloneRuntime(selected).open()
    try:
        await runtime.workspaces.initialize()
        assert runtime.records.get("repository/setup")[1]["base_branch"] == "feature"
        assert git(source, "branch", "--show-current") == original
        AgentServices(runtime, selected).process("worker", "worker")
        await runtime.workspaces.create(
            "ordinary",
            "worker",
            "ordinary",
            CodeRevision.model_validate(
                runtime.workspaces.code(
                    await runtime.workspaces.tree(git(source, "rev-parse", "HEAD")),
                    git(source, "rev-parse", "HEAD"),
                )
            ),
            ["a.py"],
            ["a.py"],
        )
        with pytest.raises(ValueError, match="workspace grant"):
            await runtime.workspaces.select_branch("ordinary", "feature")
    finally:
        await runtime.close()


async def test_ten_development_tasks_include_one_cloud_coder_with_shared_shell_tools(config):
    source = Path(config.repository)
    names = ["part" + str(i) for i in range(10)]
    for name in names:
        (source / (name + ".py")).write_text("VALUE = 1\n")
    git(source, "add", ".")
    git(source, "-c", "user.name=Test", "-c", "user.email=test@localhost", "commit", "-qm", "ten tasks")
    config = config.model_copy(
        update={
            "allowed_write_paths": [name + ".py" for name in names],
            "closure_paths": [name + ".py" for name in names],
            "shell_execution": "trusted",
            "limits": config.limits.model_copy(update={"max_input_tokens_per_call": 96000}),
            "local": config.local.model_copy(
                update={"max_context_tokens": 128000, "reserved_context_tokens": 256000}
            ),
            "cloud": config.cloud.model_copy(
                update={
                    "protocol": "codex_app_server",
                    "brokered_tools": True,
                    "max_context_tokens": 128000,
                    "reserved_context_tokens": 256000,
                }
            ),
        }
    )
    runtime = await StandaloneRuntime(config).open()
    junior = ScriptedAgent(two=False)
    coding = []

    class Cloud:
        assessment_mutated = False

        async def generate_job(self, messages, snapshot, schema, callback=None):
            data = pinned(messages)
            if "assignment" in data:
                coding.append(data)
                assert data["assignment"]["task_id"] == "part7"
                assert "shell.run" in data["available_tools"]
                if data["phase"] == "development":
                    observation = await callback(
                        "senior-write",
                        {"tool": "shell.run", "arguments": {"script": "printf 'VALUE = 2\\n' > part7.py"}},
                    )
                    assert observation["state"] == "succeeded", observation
                if data["phase"] == "assessment" and not self.assessment_mutated:
                    self.assessment_mutated = True
                    observation = await callback(
                        "assessment-edit",
                        {"tool": "shell.run", "arguments": {"script": "printf '# assessed\\n' >> part7.py"}},
                    )
                    assert observation["state"] == "succeeded", observation
                reply = (
                    {"kind": "assessment", "verdict": "successful", "summary": "Assessed"}
                    if data["phase"] == "assessment"
                    else {"kind": "candidate", "summary": "Ready"}
                )
            elif not data["all_task_ids"]:
                reply = {
                    "goal": "Update ten values",
                    "tasks": [
                        {
                            "task_id": name,
                            "objective": "Update " + name,
                            "write_paths": [name + ".py"],
                            "read_paths": [name + ".py"],
                            "checks": ["syntax"],
                            "role": "specialist" if name == "part7" else "worker",
                        }
                        for name in names
                    ],
                }
            else:
                reply = {
                    "goal": "Finished",
                    "complete": True,
                    "completion_assessment": fixture_completion(data),
                    "dispositions": [
                        {"report_ref": r["record_id"], "action": "keep", "reason": "Checked"}
                        for r in data["reports"]
                    ],
                }
            return {
                "text": json.dumps(fixture_review_reply(reply, data)),
                "model": "cloud-fixture",
                "usage": {"total_tokens": 50},
                "events": [],
            }

        async def close(self):
            pass

    for client in runtime.clients.values():
        await client.close()
    runtime.clients = {"local": junior, "cloud": Cloud()}
    app = AgentServices(runtime, config)
    original_model = app.model
    replay_checked = []

    async def model_with_replay(state, senior=False):
        reply = await original_model(state, senior)
        if not senior and state["phase"] == "assessment" and reply.get("repair"):
            replay = await original_model(state, senior)
            assert replay.get("repair") is True
            replay_checked.append(True)
        return reply

    app.model = model_with_replay
    try:
        result = await ProjectAgent(app).run()
        assert result["outcome"] == "completed", app.get("app/run")
        assignments = [task["assignment"] for _, _, task in runtime.records.scan("task/")]
        assert sum(t["role"] == "specialist" for t in assignments) == 1
        assert sum(t["role"] == "worker" for t in assignments) == 9
        assert {data["phase"] for data in coding} == {"development", "reconciliation", "assessment"}
        reports = [report for _, _, report in runtime.records.scan("report/")]
        assert len(reports) == 10
        tree = await runtime.workspaces.tree(app.get("head/provisional")["code"]["commit_id"])
        assert all(
            tree[name + ".py"][1] == (b"VALUE = 2\n# assessed\n" if name == "part7" else b"VALUE = 2\n")
            for name in names
        )
        assert replay_checked
        assert sum(data["phase"] == "assessment" for data in coding) == 2
        for _, _, effect in runtime.records.scan("effect/"):
            request = effect["request"]
            if request["payload"]["kind"] in {"agent_job", "model_query"}:
                backend = effect["result"]["actual_backend"]["backend_id"]
                assert backend == ("local" if request["payload"]["role"] == "worker" else "cloud")
    finally:
        await runtime.close()


async def test_shell_is_journaled_bounded_and_restores_out_of_scope_changes(config):
    config = config.model_copy(update={"shell_execution": "trusted"})
    runtime = await StandaloneRuntime(config).open()
    app = AgentServices(runtime, config)
    try:
        await ProjectAgent(app).initialize()
        app.process("shell-worker", "worker")
        base = CodeRevision.model_validate(app.get("head/initial")["code"])
        await runtime.workspaces.create(
            "shell-view", "shell-worker", "test", base, ["a.py"], ["a.py", "b.py"]
        )
        state = {"process_id": "shell-worker", "workspace_id": "shell-view", "logical_step": 0}

        async def call(step, script, **kwargs):
            manifest = runtime.workspaces.current("shell-view")
            return await app.capability(
                state,
                step,
                "shell.run",
                {"script": script, "generation": manifest.generation, **kwargs},
                "private_write",
            )

        result, observation = await call("append", "printf '# once\\n' >> a.py; printf 'done'")
        assert result.state == "succeeded" and observation["stdout"] == "done"
        _, replay = await call("append", "printf '# once\\n' >> a.py; printf 'done'")
        assert replay == observation
        root = runtime.workspaces.root_for(runtime.workspaces.current("shell-view"))
        assert (root / "a.py").read_text().count("# once") == 1
        result, observation = await call("scope", "printf 'bad' > b.py")
        assert result.state == "failed" and "scope" in observation["error"]
        assert (root / "b.py").read_text() == "VALUE = 1\n"
        result, observation = await call("timeout", "sleep 30", timeout_seconds=0.05)
        assert result.state == "succeeded" and observation["timed_out"]
        assert runtime.records.get("permit/shell/installation")[1]["process_id"] is None
        result, observation = await call("cwd", "pwd", cwd="../")
        assert result.state == "failed" and "cwd" in observation["error"]
        result, observation = await call("output", "python3 -c 'print(chr(120) * 300000)'")
        assert result.state == "succeeded" and observation["truncated"]
        assert len(observation["stdout"].encode()) <= config.limits.max_output_bytes
        assert (Path(config.repository) / "a.py").read_text() == "VALUE = 1\n"
    finally:
        await runtime.close()


async def test_missing_discovered_checks_cannot_be_published_as_success(config):
    selected = AgentConfig.model_validate({
        **config.model_dump(), "checks": [], "prepare_repository": True, "max_sprints": 2,
    })

    class Unverified:
        async def generate(self, messages, max_output, response_schema=None):
            data = pinned(messages)
            if "assignment" in data:
                reply = (
                    {"kind": "assessment", "verdict": "successful", "summary": "Unverified claim"}
                    if data["phase"] == "assessment" else {"kind": "candidate", "summary": "Ready"}
                )
            else:
                reply = {
                    "goal": "Claim completion", "complete": True,
                    "dispositions": [
                        {"report_ref": r["record_id"], "action": "keep", "reason": "Reviewed"}
                        for r in data["reports"]
                    ],
                }
            return {"text": json.dumps(fixture_review_reply(reply, data)), "model": "fixture", "usage": {"total_tokens": 50}}

        async def close(self):
            pass

    runtime = await StandaloneRuntime(selected).open()
    try:
        for client in runtime.clients.values():
            await client.close()
        runtime.clients = {"local": Unverified(), "cloud": Unverified()}
        app = AgentServices(runtime, selected)
        outcome = await asyncio.wait_for(ProjectAgent(app).run(), 20)
        assert outcome["outcome"] != "completed"
        task = app.get("task/project_setup")
        assert app.get(task["report_ref"])["verdict"] == "uncertain"
        assert not runtime.records.scan("acceptance-receipt/")
    finally:
        await runtime.close()


@pytest.mark.parametrize("filename,content", [
    ("main.py", "print('hello')\n"),
    ("package.json", '{"scripts":{"test":"node --test"}}'),
])
def test_ui_leaves_check_selection_to_agent_for_existing_projects(tmp_path, filename, content):
    source = tmp_path / "project"
    source.mkdir()
    (source / filename).write_text(content)
    manager = TestUI(tmp_path / "ui")
    assert manager.repository_options(str(source))["check_command"] == ""
    for command in (None, "", "   "):
        selected = manager.configure_run(str(source), command)
        assert selected.checks == [] and selected.prepare_repository
    assert manager.configure_run(str(source), "custom-check --all").checks[0].argv == ["custom-check", "--all"]
