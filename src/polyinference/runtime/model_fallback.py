"""Durable, binding-local model availability routing; no agent task semantics."""

from ..contracts import AgentJob, Feature, ModelQuery, OperationRequest
from ..primitives import canonical, digest, now, operation_fingerprint


class ModelFallback:
    def __init__(self, runtime):
        self.runtime = runtime

    def policy(self, request):
        if not isinstance(request.payload, (ModelQuery, AgentJob)):
            return None
        binding = self.runtime.config.role_bindings[request.payload.role]
        return getattr(self.runtime.config, binding).retry_model

    def root(self, request, key=None):
        if request.extensions.get("runtime/inference-root"):
            return request.extensions["runtime/inference-root"]
        if key and key.startswith("inference-attempt/"):
            return key.removeprefix("inference-attempt/").rsplit("/", 1)[0]
        return request.operation_id

    def select(self, request, key):
        """One selection per logical invocation, shared by response/transport repairs."""
        rt = self.runtime
        binding = rt.config.role_bindings[request.payload.role]
        endpoint = getattr(rt.config, binding)
        policy = endpoint.retry_model
        if not policy:
            return endpoint, rt.clients[binding], None
        alternate = request.extensions.get("runtime/model-fallback")
        root = self.root(request, key)
        selection_id = alternate["retry_operation_id"] if alternate else root
        record = "model-selection/" + selection_id
        saved = rt.records.get(record)
        if saved:
            selection = saved[1]
        else:
            state_key = "model-fallback-state/" + binding
            prior = rt.records.get(state_key)
            state = (
                dict(prior[1])
                if prior
                else {"sequence": 0, "epoch": 0, "main_failed": False, "remaining": 0, "last_main_result": 0}
            )
            if alternate:
                parent = rt.records.get("model-selection/" + root)
                sequence = parent[1]["sequence"] if parent else state["sequence"]
                use_retry, reason = True, "unavailable_retry"
            else:
                state["sequence"] += 1
                sequence = state["sequence"]
                use_retry = state["remaining"] > 0
                reason = "cooldown" if use_retry else "primary_probe" if state["main_failed"] else "primary"
                if use_retry:
                    state["remaining"] -= 1
            selection = {
                "root": root,
                "binding": binding,
                "sequence": sequence,
                "epoch": state["epoch"],
                "model": policy.model if use_retry else endpoint.model,
                "reasoning_effort": policy.reasoning_effort if use_retry else endpoint.reasoning_effort,
                "alternate": use_retry,
                "reason": reason,
            }
            expected = {record: 0}
            updated = {record: selection}
            if not alternate:
                expected[state_key] = prior[0] if prior else 0
                updated[state_key] = state
            rt.records.compare_and_publish(expected, updated)
        if selection["alternate"]:
            return rt.fallback_clients[binding].endpoint, rt.fallback_clients[binding], selection
        return endpoint, rt.clients[binding], selection

    def observe(self, request, result, *, final=False):
        rt = self.runtime
        root = self.root(request)
        selection = rt.records.get("model-selection/" + root)
        if not selection:
            return
        selected = selection[1]
        if selected["alternate"]:
            if (
                final
                and selected["reason"] == "cooldown"
                and result.extensions.get("polyinference/attempted-backend", {}).get("submitted") is False
            ):
                token = "model-fallback-unsubmitted/" + root
                state_key = "model-fallback-state/" + selected["binding"]
                prior = rt.records.get(state_key)
                if not rt.records.get(token) and prior[1]["epoch"] == selected["epoch"]:
                    state = {
                        **prior[1],
                        "remaining": min(self.policy(request).fallback_calls, prior[1]["remaining"] + 1),
                    }
                    rt.records.compare_and_publish(
                        {state_key: prior[0], token: 0},
                        {state_key: state, token: {"operation_id": result.operation_id}},
                    )
            return
        unavailable = bool(result.extensions.get("polyinference/model-unavailable"))
        if not unavailable and result.state != "succeeded":
            return
        token = "model-fallback-observed/" + root
        if rt.records.get(token):
            return
        state_key = "model-fallback-state/" + selected["binding"]
        prior = rt.records.get(state_key)
        state = dict(prior[1])
        if selected["sequence"] >= state["last_main_result"]:
            state["last_main_result"] = selected["sequence"]
            state["epoch"] += 1
            if unavailable:
                policy = self.policy(request)
                state["remaining"] = policy.fallback_calls
                state["main_failed"] = True
            else:
                state.update(main_failed=False, remaining=0)
        rt.records.compare_and_publish(
            {state_key: prior[0], token: 0},
            {state_key: state, token: {"operation_id": result.operation_id, "unavailable": unavailable}},
        )

    def authorize(self, request):
        alternate = request.extensions["runtime/model-fallback"]
        row = self.runtime.records.get("model-fallback/" + alternate["root_operation_id"])
        if not row or canonical(row[1]["request"]) != canonical(request):
            raise ValueError("Model fallback requires its durable OS-issued intent")

    def callback_root(self, request):
        alternate = request.extensions.get("runtime/model-fallback")
        return alternate["callback_root_operation_id"] if alternate else request.operation_id

    async def recover(self, request, result, *, final=False):
        """Return (handled, result). An alternate is attempted at most once per root."""
        rt = self.runtime
        policy = self.policy(request)
        if not policy:
            return False, result
        root = self.root(request)
        prior = rt.records.get("model-fallback/" + root)
        if prior:
            retry = OperationRequest.model_validate(prior[1]["request"])
            return True, await rt._execute_once(retry)
        self.observe(request, result, final=final)
        selection = rt.records.get("model-selection/" + root)
        if (
            not selection
            or selection[1]["alternate"]
            or not result.extensions.get("polyinference/model-unavailable")
        ):
            return False, result
        continuation = result.extensions.get("runtime/native-continuation")
        has_tools = isinstance(request.payload, AgentJob) and any(
            v["request"].get("causal_parent_ref") == result.operation_id
            for _, _, v in rt.records.scan("effect/")
        )
        if has_tools and not continuation:
            return True, result
        blocked = rt.model_retries._blocked(request, result, allow_native_continuation=bool(continuation))
        if blocked:
            return True, result
        operation = digest(canonical([root, "model-fallback", policy.model]))
        failed = rt.records.get("effect/" + result.operation_id)
        attempts = [
            (int(key.rsplit("/", 1)[1]), row)
            for key, _, row in rt.records.scan("inference-attempt/" + result.operation_id + "/")
            if row.get("result")
        ]
        source = max(attempts, key=lambda item: item[0])[1] if attempts else failed[1] if failed else None
        # Availability may be discovered on an output-adapted/transport attempt.
        # Continue the last physical payload, including caller response repair.
        payload = OperationRequest.model_validate(source["request"]).payload if source else request.payload
        if isinstance(payload, AgentJob) and continuation:
            payload = payload.model_copy(update={"session_ref": continuation["session_id"]})
        retry = request.model_copy(
            update={
                "operation_id": operation,
                "record_id": "request/" + operation,
                "logical_step_id": request.logical_step_id + "/model-fallback",
                "created_at": now(),
                "payload": payload,
                "required_features": [
                    *request.required_features,
                    Feature(feature_id="runtime/model-fallback", version="1"),
                ],
                "extensions": {
                    **request.extensions,
                    "runtime/inference-root": root,
                    "runtime/model-fallback": {
                        "root_operation_id": root,
                        "previous_operation_id": result.operation_id,
                        "retry_operation_id": operation,
                        "callback_root_operation_id": result.operation_id,
                    },
                },
            }
        )
        if isinstance(payload, AgentJob) and request.extensions.get("polyinference/workspace-view"):
            manifest = rt.workspaces.current(payload.workspace_id)
            if manifest.process_id != request.scope.process_id:
                raise ValueError("Native continuation workspace owner changed")
            retry = retry.model_copy(
                update={
                    "extensions": {
                        **retry.extensions,
                        "polyinference/workspace-view": {
                            "workspace_id": manifest.workspace_id,
                            "manifest_ref": manifest.manifest_id,
                            "generation": manifest.generation,
                            "view": manifest.view,
                        },
                    }
                }
            )
        retry = retry.model_copy(update={"intent_digest": operation_fingerprint(retry)})
        rt.records.put_once(
            "model-fallback/" + root,
            {"request": retry.model_dump(mode="json"), "previous_operation_id": result.operation_id},
        )
        return True, await rt._execute_once(retry)
