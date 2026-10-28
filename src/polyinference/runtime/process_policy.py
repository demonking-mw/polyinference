"""Generic registration and dispatch constraints for the static runtime profile."""

from ..contracts import AgentJob, ModelQuery, ProcessSpec


def artifacts(value):
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        if "artifact_id" in value and "classification" in value:
            yield value
        else:
            for child in value.values():
                yield from artifacts(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifacts(child)


class ProcessPolicy:
    def __init__(self, config, records):
        self.config, self.records = config, records

    def data(self, policy, endpoint, binding, inputs):
        # Unknown placement cannot satisfy a mandatory local-only/cloud-only rule.
        location = endpoint.inference_location
        if (location not in policy.allowed_inference_locations
                and not (location is None and {"local", "cloud"} <= set(policy.allowed_inference_locations))):
            raise ValueError("Inference location conflicts with mandatory process data policy")
        if binding not in policy.allowed_destination_classes:
            raise ValueError("Destination conflicts with mandatory process data policy")
        rank = {"public": 0, "project": 1, "restricted": 2}
        if any(rank[ref["classification"]] > rank[policy.maximum_classification]
               for ref in artifacts(inputs)):
            raise ValueError("Input classification exceeds mandatory process data policy")

    def distribution(self, spec, endpoint, phase=None):
        rules = [r for r in spec.schedule.distribution.rules if "*" in r.roles or spec.role in r.roles]
        if not rules or (phase is not None and not any("*" in r.phases or phase in r.phases for r in rules)):
            raise ValueError("Static allocation has no matching role/phase rule")
        for rule in rules:
            if phase is not None and "*" not in rule.phases and phase not in rule.phases:
                continue
            if rule.enforcement == "soft":
                continue
            value = endpoint.inference_location if rule.axis == "inference_location" else endpoint.protocol
            if value not in rule.eligible_classes:
                raise ValueError("Static binding cannot satisfy hard allocation class")
            if rule.target_weights and any(weight and key != value for key, weight in rule.target_weights.items()):
                raise ValueError("Unsupported hard allocation weights require dynamic scheduling")

    def register(self, spec, binding):
        if self.config.role_bindings.get(spec.role) != binding:
            raise ValueError("Process binding differs from configured static role binding")
        if spec.limits != self.config.limits:
            raise ValueError("Uniform runtime requires identical registered process limits")
        endpoint = getattr(self.config, binding)
        self.data(spec.schedule.data_policy, endpoint, binding, spec.input_refs)
        if self.config.data_policy:
            self.data(self.config.data_policy, endpoint, binding, spec.input_refs)
        self.distribution(spec, endpoint)

    def dispatch(self, request, process):
        spec = ProcessSpec.model_validate(self.records.get(process["spec_ref"])[1])
        binding = self.config.role_bindings.get(spec.role)
        self.register(spec, binding)
        if request.limits != spec.limits:
            raise ValueError("Operation limits differ from registered process authority")
        if isinstance(request.payload, (ModelQuery, AgentJob)):
            if request.payload.role != spec.role:
                raise ValueError("Operation cannot change the registered process role")
            endpoint = getattr(self.config, binding)
            self.data(spec.schedule.data_policy, endpoint, binding, request.payload)
            if self.config.data_policy:
                self.data(self.config.data_policy, endpoint, binding, request.payload)
            phase = request.payload.phase if isinstance(request.payload, ModelQuery) \
                else request.payload.required_phase_protocol
            self.distribution(spec, endpoint, phase)
