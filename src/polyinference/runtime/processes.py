"""One driver per durable process, status/wait and cooperative cancellation."""

from __future__ import annotations

import asyncio

from ..domain import now


def request_cancel(records, process_id, reason):
    process = records.get("process/" + process_id)
    if not process:
        raise ValueError("Unknown process")
    if process[1]["role"] == "senior":
        raise ValueError("Use steering for the controller; cancellation targets coding processes")
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
    run = records.get("app/run")
    if run:
        expected["app/run"] = run[0]
        updates["app/run"] = {
            **run[1],
            "starts_closed": True,
            "completion_proposed": False,
            "captured_workers": sorted(set(run[1]["active_workers"]) | set(run[1]["captured_workers"])),
        }
    records.compare_and_publish(expected, updates)


class Processes:
    def __init__(self, records, max_workers):
        self.records, self.max_workers = records, max_workers
        self.drivers = {}

    def start(self, process_id, factory):
        existing = self.drivers.get(process_id)
        if existing and not existing.done():
            return existing
        process = self.records.get("process/" + process_id)
        if not process:
            raise ValueError("Unregistered process")
        if process[1]["role"] != "senior":
            residents = sum(
                not task.done() and self.records.get("process/" + pid)[1]["role"] != "senior"
                for pid, task in self.drivers.items()
            )
            if residents >= self.max_workers:
                raise RuntimeError("Resident worker capacity is full")
        self.drivers[process_id] = asyncio.create_task(factory(), name=process_id)
        return self.drivers[process_id]

    def status(self, process_id):
        status = self.records.get("process-status/" + process_id)
        if not status:
            raise ValueError("Unknown process")
        return status[1]

    def cancel(self, process_id, reason="operator cancellation"):
        request_cancel(self.records, process_id, reason)

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
