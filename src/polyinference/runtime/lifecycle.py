"""Generic process settlement and inherited resource accounts, without task policy."""

from datetime import datetime, timedelta

from ..domain import now


class ProcessLifecycle:
    def account(self, process_id):
        saved = self.records.get("process-account/" + process_id)
        return saved[1]["root"] if saved else process_id

    def bind_recovery(self, process_id, predecessor, *, require_park=True):
        key = "process-account/" + process_id
        existing = self.records.get(key)
        if existing:
            if existing[1]["predecessor"] != predecessor:
                raise ValueError("Process recovery lineage is immutable")
            return
        if self.records.scan("effect/") and any(
            body["request"]["scope"]["process_id"] == process_id
            for _, _, body in self.records.scan("effect/")
        ):
            raise ValueError("Recovery binding must precede execution")
        receipt = self.records.get("process-parked/" + predecessor)
        parent = self.records.get("process/" + predecessor)
        child = self.records.get("process/" + process_id)
        if (require_park and not receipt) or not parent or not child or child[1]["state"] != "ready":
            raise ValueError("Recovery needs a fenced predecessor and a new process")
        parent_spec = self.records.get(parent[1]["spec_ref"])[1]
        child_spec = self.records.get(child[1]["spec_ref"])[1]
        if (
            parent_spec["grant_ref"] != child_spec["grant_ref"]
            or parent_spec["limits"] != child_spec["limits"]
        ):
            raise ValueError("Recovery cannot change grants or resource limits")
        inherited = self.records.get("process-account/" + predecessor)
        cutoff = (
            inherited[1]["deadline"]
            if inherited
            else (
                datetime.fromisoformat(parent[1]["started_at"])
                + timedelta(milliseconds=parent_spec["limits"]["max_wall_time_ms"])
            ).isoformat()
        )
        self.records.put_once(
            key,
            {
                "root": self.account(predecessor),
                "predecessor": predecessor,
                "deadline": cutoff,
                "limits": parent_spec["limits"],
                "grant_ref": parent_spec["grant_ref"],
            },
        )

    def process_deadline(self, process_id):
        row = self.records.get("process-account/" + process_id)
        return datetime.fromisoformat(row[1]["deadline"]) if row else None

    def settlement(self, process_id):
        """Retained execution facts, including prepared work; never infer remote termination."""
        pending = []
        for key, _, value in self.records.scan("effect/"):
            if value["request"]["scope"]["process_id"] != process_id:
                continue
            result = value.get("result")
            if (
                not result
                or result["execution_termination"] != "confirmed_stopped"
                or result["effects"] == "unknown"
            ):
                pending.append(key[7:])
        inflight = [
            operation_id
            for operation_id, future in self.inflight.items()
            if not future.done()
            and (self.records.get("effect/" + operation_id) or (0, {}))[1]
            .get("request", {})
            .get("scope", {})
            .get("process_id")
            == process_id
        ]
        permits = [
            key for key, _, value in self.records.scan("permit/") if value.get("process_id") == process_id
        ]
        return {
            "process_id": process_id,
            "pending_operations": sorted(set(pending + inflight)),
            "permit_refs": permits,
        }

    def park_process(self, process_id):
        key = "process-parked/" + process_id
        retained = self.records.get(key)
        if retained:
            return retained[1]
        facts = self.settlement(process_id)
        if self.uncertain() or facts["pending_operations"] or facts["permit_refs"]:
            raise RuntimeError("Process cannot be fenced with unsettled effects or owned permits")
        process_key = "process/" + process_id
        revision, process = self.records.get(process_key)
        receipt = {
            **facts,
            "owner_generation": process["owner_generation"] + 1,
            "parked_at": now().isoformat(),
        }
        self.records.compare_and_publish(
            {process_key: revision},
            {process_key: {**process, "state": "paused", "owner_generation": receipt["owner_generation"]}},
            {key: receipt},
        )
        return receipt

    def prepare_effect(self, request, effect_key, effect):
        """Count new logical operations once across replacement identities; replay is free."""
        key = "budget/steps/" + self.account(request.scope.process_id)
        retained = self.records.get(key)
        used = retained[1]["used"] if retained else 0
        if used >= request.limits.max_steps:
            raise ValueError("Shared logical operation allowance exhausted")
        self.records.compare_and_publish(
            {key: retained[0] if retained else 0, effect_key: 0},
            {key: {"used": used + 1}, effect_key: effect},
        )
