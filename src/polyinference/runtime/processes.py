"""One driver per durable process, status/wait and cooperative cancellation."""

from __future__ import annotations

import asyncio
import uuid

from ..primitives import now


def request_resume(records, process_id=None, text=None, *, request_id=None):
    """Record an operator signal; the owning application supplies continuation policy."""
    if text is not None and (not isinstance(text, str) or len(text) > 16000):
        raise ValueError("Steering instructions must be at most 16000 characters")
    if request_id is not None and (not isinstance(request_id, str) or not 1 <= len(request_id) <= 128):
        raise ValueError("Resume request ID must be a nonempty string of at most 128 characters")
    from ..primitives import digest

    request_id = request_id if request_id is not None else uuid.uuid4().hex
    key = "resume-request/" + digest(request_id.encode())[7:]
    content = {"process_id": process_id, "text": (text or "").strip(), "request_id": request_id}
    previous = records.get(key)
    if previous:
        if any(previous[1].get(field) != value for field, value in content.items()):
            raise ValueError("Resume request ID was already used for different instructions")
        return key
    if process_id is None:
        if not any(body.get("state") in {"paused", "running", "ready"} for _, _, body in records.scan("process/")):
            raise ValueError("This execution has no paused process")
        control_key = "resume-control/run"
        control = records.get(control_key)
        records.compare_and_publish(
            {control_key: control[0] if control else 0},
            {control_key: {"resume_request_ref": key}},
            {key: {**content, "requested_at": now().isoformat()}},
        )
        return key
    if not isinstance(process_id, str):
        raise ValueError("Invalid process ID")
    process = records.get("process/" + process_id)
    if not process or process[1].get("state") != "paused":
        raise ValueError("Select a paused process to resume")
    control_key = "process-control/" + process_id
    control = records.get(control_key)
    if control and control[1].get("cancel_requested"):
        raise ValueError("A cancelled process cannot be resumed")
    # Acceptance records intent only. Preparation and dispatch still enforce
    # effect certainty before allowing any new execution.
    records.compare_and_publish(
        {"process/" + process_id: process[0], control_key: control[0] if control else 0},
        {control_key: {**(control[1] if control else {}), "resume_request_ref": key}},
        {key: {**content, "requested_at": now().isoformat()}},
    )
    return key


def request_cancel(records, process_id, reason):
    process = records.get("process/" + process_id)
    if not process:
        raise ValueError("Unknown process")
    if process[1].get("management", False):
        raise ValueError("Use the owning agent's control interface for management processes")
    if process[1]["state"] in {"completed", "cancelled"}:
        return
    key = "process-control/" + process_id
    prior = records.get(key)
    status_key = "process-status/" + process_id
    status = records.get(status_key)
    expected = {key: prior[0] if prior else 0}
    updates = {key: {"cancel_requested": True, "reason": reason, "requested_at": now().isoformat()}}
    if status:
        expected[status_key] = status[0]
        updates[status_key] = {
            **status[1],
            "revision": status[1]["revision"] + 1,
            "cancellation_requested": True,
        }
    records.compare_and_publish(expected, updates)


class Processes:
    def __init__(self, records, max_workers, policy=None):
        self.records, self.max_workers = records, max_workers
        self.policy = policy
        self.drivers = {}
        self.on_cancel = None

    def register(self, spec, binding_ref, *, management=False, capabilities=()):
        from ..contracts import ProcessStatus

        if self.policy:
            self.policy.register(spec, binding_ref)

        key = "process/" + spec.process_id
        status = ProcessStatus(
            record_id="process-status/" + spec.process_id, revision=1,
            scope=spec.scope, created_at=now(), process_spec_ref=spec.record_id,
            state="ready", phase=spec.entry_point, owner_generation=1,
            binding_generation=1, binding_ref=binding_ref, wait=None,
            pending_operations=[], reservation_refs=[], permit_refs=[],
            continuation_ref=None, terminal_result_ref=None, cancellation_requested=False,
        )
        self.records.compare_and_publish(
            {key: 0, status.record_id: 0},
            {key: {"process_id": spec.process_id, "role": spec.role, "management": management,
                   "owner_generation": 1, "state": "ready", "spec_ref": spec.record_id,
                   "started_at": now().isoformat(),
                   "task_ref": spec.task_spec_ref,
                   "capabilities": list(capabilities)},
             status.record_id: status.model_dump(mode="json")},
            {spec.record_id: spec.model_dump(mode="json")},
        )

    def start(self, process_id, factory):
        existing = self.drivers.get(process_id)
        if existing and not existing.done():
            return existing
        process = self.records.get("process/" + process_id)
        if not process:
            raise ValueError("Unregistered process")
        if process[1]["state"] in {"completed", "failed", "cancelled", "paused"}:
            raise ValueError("Process is stopped; explicit recovery is required")
        self.admit(process_id)
        async def drive():
            try:
                key = "process/" + process_id
                current = self.records.get(key)
                self.records.compare_and_publish({key: current[0]}, {key: {**current[1], "state": "running"}})
                spec = self.records.get(process[1].get("spec_ref", ""))
                if spec and spec[1].get("limits"):
                    from datetime import datetime

                    deadline = datetime.fromisoformat(process[1].get("started_at", spec[1]["created_at"]).replace("Z", "+00:00")).timestamp()
                    cutoff = deadline + spec[1]["limits"]["max_wall_time_ms"] / 1000
                    inherited = self.records.get("process-account/" + process_id)
                    if inherited:
                        cutoff = min(cutoff, datetime.fromisoformat(inherited[1]["deadline"]).timestamp())
                    remaining = cutoff - now().timestamp()
                    result = await asyncio.wait_for(factory(), max(0, remaining))
                else:
                    result = await factory()
                status = self.records.get("process-status/" + process_id)
                if status and status[1]["state"] not in {"completed", "cancelled", "failed", "paused"}:
                    control = self.records.get("process-control/" + process_id)
                    self.finish(process_id, state="cancelled" if control and control[1].get("cancel_requested") else "completed")
                elif status and status[1]["state"] in {"completed", "cancelled", "failed"}:
                    residency = self.records.get("process-residency/" + process_id)
                    if residency and residency[1]["state"] == "resident":
                        current = self.records.get("process/" + process_id)
                        self.finish(process_id, state=status[1]["state"],
                                    output_refs=current[1].get("output_refs", ()))
                return result
            except BaseException:
                status = self.records.get("process-status/" + process_id)
                if status and status[1]["state"] not in {"completed", "cancelled", "failed", "paused"}:
                    control = self.records.get("process-control/" + process_id)
                    state = "cancelled" if control and control[1].get("cancel_requested") else "paused"
                    try:
                        self.finish(process_id, state=state)
                    except ValueError:
                        self.finish(process_id, state="paused")
                raise

        self.drivers[process_id] = asyncio.create_task(drive(), name=process_id)
        return self.drivers[process_id]

    def finish(self, process_id, *, state="completed", output_refs=()):
        """Terminate an OS process; artifacts and even an empty result are valid."""
        if state not in {"completed", "cancelled", "failed", "paused"}:
            raise ValueError("Process finish requires a terminal or paused state")
        process_key, status_key = "process/" + process_id, "process-status/" + process_id
        process, status = self.records.get(process_key), self.records.get(status_key)
        if not process or not status:
            raise ValueError("Unknown process")
        unsettled = [body for _, _, body in self.records.scan("effect/")
                     if body["request"]["scope"].get("process_id") == process_id
                     and body["state"] in {"prepared", "submitting", "active", "uncertain"}]
        if unsettled and state != "paused":
            raise ValueError("Process has unsettled effects")
        if state == "completed" and any(
            body.get("process_id") == process_id for _, _, body in self.records.scan("permit/")
        ):
            raise ValueError("Process still owns a resource permit")
        expected = {process_key: process[0], status_key: status[0]}
        updates = {
                process_key: {**process[1], "state": state,
                              "output_refs": [ref.model_dump(mode="json") if hasattr(ref, "model_dump") else ref
                                              for ref in output_refs]},
                status_key: {**status[1], "state": state, "revision": status[1]["revision"] + 1,
                             "last_progress_at": now().isoformat()},
            }
        residency = self.records.get("process-residency/" + process_id)
        if state != "paused" and residency:
            expected["process-residency/" + process_id] = residency[0]
            updates["process-residency/" + process_id] = {**residency[1], "state": "released"}
        self.records.compare_and_publish(expected, updates)

    def admit(self, process_id):
        process = self.records.get("process/" + process_id)
        if not process:
            raise ValueError("Unknown process")
        if process[1].get("management", False):
            return
        key = "process-residency/" + process_id
        prior = self.records.get(key)
        if prior and prior[1]["state"] == "resident":
            return
        residents = sum(row["state"] == "resident"
                        for _, _, row in self.records.scan("process-residency/"))
        if residents >= self.max_workers:
            raise RuntimeError("Resident worker capacity is full; explicit safe hibernation is required")
        self.records.compare_and_publish(
            {key: prior[0] if prior else 0},
            {key: {"state": "resident", "generation": (prior[1]["generation"] if prior else 0) + 1}},
        )

    def hibernate(self, process_id):
        process = self.records.get("process/" + process_id)
        if not process or process[1]["state"] != "paused":
            raise ValueError("Only a paused process can hibernate")
        driver = self.drivers.get(process_id)
        if driver and not driver.done() and not self.records.get("process-parked/" + process_id):
            raise ValueError("Active driver must settle or be explicitly fenced before hibernation")
        if any(row["request"]["scope"].get("process_id") == process_id
               and (not row.get("result") or row["result"]["execution_termination"] != "confirmed_stopped"
                    or row["result"]["effects"] == "unknown")
               for _, _, row in self.records.scan("effect/")):
            raise ValueError("Hibernation requires settled effects")
        if any(row.get("process_id") == process_id for _, _, row in self.records.scan("permit/")):
            raise ValueError("Hibernation requires released resource permits")
        if any(row.get("process_id") == process_id and row.get("state") in {"waiting", "held"}
               for _, _, row in self.records.scan("reservation/")):
            raise ValueError("Hibernation requires settled physical reservations")
        key = "process-residency/" + process_id
        prior = self.records.get(key)
        if prior and prior[1]["state"] == "hibernated":
            return
        self.records.compare_and_publish(
            {"process/" + process_id: process[0], key: prior[0] if prior else 0},
            {key: {"state": "hibernated", "generation": prior[1]["generation"] if prior else 0,
                   "continuation_ref": self.status(process_id).get("continuation_ref")}},
        )

    def status(self, process_id):
        status = self.records.get("process-status/" + process_id)
        if not status:
            raise ValueError("Unknown process")
        return status[1]

    def cancel(self, process_id, reason="operator cancellation"):
        request_cancel(self.records, process_id, reason)
        if self.on_cancel:
            self.on_cancel(process_id)

    async def wait(self, process_id, timeout=None):
        async def terminal():
            while True:
                self.records.changed.clear()
                value = self.status(process_id)
                if value["state"] in {"completed", "cancelled", "failed", "paused"}:
                    return value
                await self.records.changed.wait()

        return await asyncio.wait_for(terminal(), timeout)

    async def close(self):
        tasks = [task for task in self.drivers.values() if not task.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
