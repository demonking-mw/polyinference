from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import ScriptedAgent, git

from polyinference.agent.controller import ProjectAgent
from polyinference.agent.routing import allocate
from polyinference.agent.services import AgentServices
from polyinference.contracts import CodeRevision, TaskSpec
from polyinference.domain import Assignment
from polyinference.runtime.adapter import StandaloneRuntime
from polyinference.ui import TestUI


def pinned(messages):
    return json.loads(
        next(m["content"] for m in messages if "Pinned application inputs:" in m["content"]).split(
            "Pinned application inputs:\n", 1
        )[1]
    )


async def test_cloud_setup_selects_requested_branch_runs_shell_and_publishes_before_planning(config):
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
            return {
                "text": json.dumps(reply),
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
        assert len(children) == 2
        assert git(source, "branch", "--show-current") == original
        assert not (source / "setup.txt").exists()
        assert git(source, "status", "--porcelain") == ""
    finally:
        await runtime.close()


@pytest.mark.parametrize("empty", [False, True])
async def test_prepare_initializes_private_git_for_plain_folder_without_tracking_secrets(
    config, tmp_path, empty
):
    source = tmp_path / "new-project"
    source.mkdir()
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
            await runtime.workspaces.create(
                task["workspace_id"], task["process_id"], task["spec_ref"], code, ["README.md"], []
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


async def test_ui_accepts_plain_project_folder_and_preserves_explicit_branch(config, tmp_path):
    source = tmp_path / "plain"
    source.mkdir()
    manager = TestUI(tmp_path / "ui")
    options = manager.repository_options(str(source))
    assert options["repository"] == str(source) and options["file_count"] == 0
    selected = manager.configure_run(str(source), "python3 -m unittest")
    assert selected.prepare_repository and selected.write_scope == "project"
    assert selected.role_bindings["specialist"] == "cloud"
    assert selected.shell_execution == "trusted"
    assert selected.cloud.brokered_tools


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
        with pytest.raises(ValueError, match="initial setup"):
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
                    "dispositions": [
                        {"report_ref": r["record_id"], "action": "keep", "reason": "Checked"}
                        for r in data["reports"]
                    ],
                }
            return {
                "text": json.dumps(reply),
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
