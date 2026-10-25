"""Read-only observations of local execution, admission and optional runtime maps."""

import inspect
import re
from datetime import datetime, timedelta

from ..domain import canonical, digest, now


class ExecutionProgress:
    def resource_state(self, process_id):
        process = self.records.get("process/" + process_id)
        if not process:
            raise ValueError("Unknown process principal")
        spec = self.records.get(process[1]["spec_ref"])[1]
        limits = spec["limits"]
        root = self.account(process_id)
        steps = (self.records.get("budget/steps/" + root) or (0, {"used": 0}))[1]["used"]
        tokens = (self.records.get("budget/process/" + root) or (0, {"reserved_or_used": 0}))[1][
            "reserved_or_used"
        ]
        cutoff = self.process_deadline(process_id) or (
            datetime.fromisoformat(process[1]["started_at"])
            + timedelta(milliseconds=limits["max_wall_time_ms"])
        )
        return {
            "account": root,
            "deadline": cutoff.isoformat(),
            "remaining_model_calls": max(
                0, limits["max_model_calls"] - self.inference_calls_used(process_id)
            ),
            "remaining_operations": max(0, limits["max_steps"] - steps),
            "remaining_tokens": max(0, limits["max_total_tokens"] - tokens),
        }

    def register_progress_source(self, name, source):
        """Host-owned, bounded synchronous inspectors; they must not perform I/O."""
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", name) or name in self.progress_sources:
            raise ValueError("Progress source needs a unique stable name")
        self.progress_sources[name] = source

    async def progress(self, process_id):
        retained = self.records.get("process/" + process_id)
        if not retained:
            raise ValueError("Unknown process principal")
        process = retained[1]
        status = (self.records.get("process-status/" + process_id) or (0, {}))[1]
        resources = self.resource_state(process_id)
        effects = []
        for key, revision, value in self.records.scan("effect/"):
            request = value["request"]
            if request["scope"]["process_id"] != process_id:
                continue
            result = value.get("result")
            effects.append(
                {
                    "operation_id": key[7:],
                    "revision": revision,
                    "state": value["state"],
                    "logical_step_id": request["logical_step_id"],
                    "payload_kind": request["payload"]["kind"],
                    "capability": request["payload"].get("capability_id"),
                    "arguments_ref": request["payload"].get("arguments"),
                    "output_refs": result["output_refs"] if result else [],
                    "execution_termination": result["execution_termination"] if result else "unknown",
                    "effects": result["effects"] if result else "unknown",
                    "created_at": request["created_at"],
                }
            )
        effects.sort(key=lambda value: (value["created_at"], value["operation_id"]))
        endpoints = {
            name: {
                "capacity": gate.limit,
                "active_or_unsettled": gate.active,
                "queued": sum(len(queue) for queue in gate.queues),
                "reserved_tokens": gate.tokens,
                "token_capacity": gate.token_limit,
                "readiness": "unprobed",
            }
            for name, gate in self.admission.items()
        }
        sources = {}
        for name, source in self.progress_sources.items():
            try:
                facts = source(process_id)
                if inspect.isawaitable(facts):
                    if inspect.iscoroutine(facts):
                        facts.close()
                    raise TypeError("Progress inspectors must be synchronous and read-only")
                canonical(facts)
                sources[name] = {"status": "available", "facts": facts}
            except Exception as exc:
                sources[name] = {"status": "unavailable", "error": type(exc).__name__}
        body = {
            "process_id": process_id,
            "state": status.get("state", process["state"]),
            "phase": status.get("phase"),
            "wait": status.get("wait"),
            "owner_generation": process["owner_generation"],
            "binding": self.config.role_bindings[process["role"]],
            "settlement": self.settlement(process_id),
            "dispatch_blocked_by_uncertainty": bool(self.uncertain()),
            "physical_model_calls": self.inference_calls_used(process_id),
            "resource_account": self.account(process_id),
            "deadline": resources["deadline"],
            "resources": resources,
            "effect_count": len(effects),
            "recent_effects": effects[-32:],
            "endpoints": endpoints,
            "sources": sources,
        }
        return {**body, "cursor": digest(canonical(body)), "observed_at": now().isoformat()}
