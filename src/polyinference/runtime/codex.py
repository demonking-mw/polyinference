"""Schema-driven native agent jobs with optional brokered capabilities.

Native events remain observations. Each phase starts a fresh native thread;
only actual dynamic-tool callbacks execute host capabilities.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from collections import Counter, deque
from pathlib import Path

from .inference import EndpointError, HTTPInference, IncompleteGeneration, UnknownExecution, model_unavailable

# Completed items carry the authoritative text. Retaining their streaming
# fragments makes the lifecycle-event bound depend on a reply's token count.
STREAMED_TEXT_METHODS = (
    "item/agentMessage/delta",
    "item/plan/delta",
    "item/reasoning/summaryTextDelta",
    "item/reasoning/summaryPartAdded",
    "item/reasoning/textDelta",
    "item/commandExecution/outputDelta",
    "item/fileChange/outputDelta",
)


class NativeJobStopped(EndpointError):
    """The app-server rejected dispatch or explicitly confirmed a terminal turn."""

    def __init__(self, message, *, retryable=True, output_failure=False):
        super().__init__(message)
        self.retryable = retryable
        self.diagnostics = ({"category": "model_output", "fault_scope": "response",
                             "reason": "invalid_native_output"} if output_failure else {})


class NativeEventLog:
    """Bounded observations; telemetry retention never controls job execution."""

    def __init__(self, byte_limit, event_limit=2000):
        self.byte_limit, self.event_limit = byte_limit, event_limit
        self.events = deque()
        self.retained_bytes = self.received_bytes = self.received_events = 0
        self.dropped_events = 0
        self.methods = Counter()
        self.recent = deque(maxlen=24)

    def record(self, message, size):
        method = str(message.get("method", ""))[:120]
        self.received_events += 1
        self.received_bytes += size
        # Bound method cardinality as well as the payload buffer.
        bucket = method if method in self.methods or len(self.methods) < 32 else "other"
        self.methods[bucket] += 1
        self.recent.append({"method": method, "bytes": size})
        if method in STREAMED_TEXT_METHODS or method.endswith("/delta") or size > self.byte_limit:
            self.dropped_events += 1
            return
        self.events.append((message, size))
        self.retained_bytes += size
        while len(self.events) > self.event_limit or self.retained_bytes > self.byte_limit:
            _, removed = self.events.popleft()
            self.retained_bytes -= removed
            self.dropped_events += 1

    def snapshot(self):
        return [message for message, _ in self.events]

    def diagnostics(self):
        # No prompt, output text, or tool arguments in failure diagnostics.
        return {
            "received_events": self.received_events, "received_bytes": self.received_bytes,
            "retained_events": len(self.events), "retained_bytes": self.retained_bytes,
            "dropped_events": self.dropped_events, "event_limit": self.event_limit,
            "byte_limit": self.byte_limit, "methods": dict(self.methods),
            "recent_events": list(self.recent),
        }


def native_context(messages):
    """Render canonical context without promoting retrieved data into instructions.

    Only the native transport uses this renderer. Ordinary API clients retain
    the canonical system/user/assistant message list and its actual roles.
    """
    instructions, inputs = [], []
    for message in messages:
        role, content = message["role"], message["content"]
        if role == "system":
            instructions.append(content)
        else:
            label = (
                "Recorded assistant output (context data)"
                if role == "assistant"
                else "Task/context or recorded observation"
            )
            inputs.append({"type": "text", "text": label + ":\n" + content})
    return "\n\n".join(instructions), inputs


def strict_output_schema(schema):
    """Translate the application grammar to Codex's strict JSON-schema subset."""

    def strict(value):
        if isinstance(value, list):
            return [strict(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {
            ("anyOf" if key == "oneOf" else key): strict(item)
            for key, item in value.items()
            if key not in {"default", "discriminator"}
        }
        if result.get("type") == "object":
            result["additionalProperties"] = False
            result["required"] = list(result.get("properties", {}))
        return result

    output = strict(schema)
    wrapped = output.get("type") != "object"
    if wrapped:
        definitions = output.pop("$defs", None)
        output = {
            "type": "object",
            "properties": {"reply": output},
            "required": ["reply"],
            "additionalProperties": False,
            **({"$defs": definitions} if definitions else {}),
        }
    return output, wrapped


def broker_schema(tools):
    definitions, schemas = {}, []
    for index, tool in enumerate(tools):
        prefix = f"capability_{index}_"

        def namespace(value):
            if isinstance(value, list):
                return [namespace(item) for item in value]
            if not isinstance(value, dict):
                return value
            return {key: "#/$defs/" + prefix + item[8:]
                    if key == "$ref" and item.startswith("#/$defs/") else namespace(item)
                    for key, item in value.items()}

        schema = dict(tool["input_schema"])
        definitions.update({prefix + name: namespace(value) for name, value in schema.pop("$defs", {}).items()})
        schemas.append(namespace(schema))
    schema = {"type": "object", "properties": {
        "tool": {"type": "string", "enum": [tool["name"] for tool in tools]},
        "arguments": {"anyOf": schemas},
    }, "required": ["tool", "arguments"], "additionalProperties": False}
    if definitions:
        schema["$defs"] = definitions
    return strict_output_schema(schema)[0]


class CodexAppServer:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.output_cap = 4 * 1024 * 1024

    def prepare(self, messages, schema, *, tools=None, instructions="", max_output=4000):
        output_schema, wrapped = strict_output_schema(schema)
        if wrapped:
            messages = [
                *messages,
                {
                    "role": "system",
                    "content": 'Return the final phase JSON inside {"reply": ...}, as required by the output schema.',
                },
            ]
        developer = ("The native filesystem view is read-only input and may be stale. "
            "All current file reads, source edits and commands must go through polyinference_tool when granted. "
            "Never use native shell, apply_patch or other native tools to write files. "
            "Never request escalated access. Only the host owns workspace generations, checks and publication. "
            + instructions + f" Return a small complete response; the requested output allowance is {max_output} tokens.")
        if instructions:
            messages = [*messages, {"role": "system", "content": instructions}]
        rendered, inputs = native_context(messages)
        developer += "\n\n" + rendered
        wire = {"input": inputs,
                "outputSchema": output_schema, "developerInstructions": developer, "wrapped": wrapped}
        if tools:
            wire["dynamicTools"] = [{"type": "function", "name": "polyinference_tool",
                "description": "Invoke one of the explicitly granted host capabilities.",
                "inputSchema": broker_schema(tools)}]
        return wire

    async def generate_job(self, messages, snapshot, schema, callback=None, observer=None,
                           *, tools=None, instructions="", max_output=4000, prepared=None, session_ref=None):
        if callback and not tools:
            raise NativeJobStopped("Brokered jobs require explicitly granted tool descriptors")
        wire = prepared or self.prepare(messages, schema, tools=tools, instructions=instructions, max_output=max_output)
        output_schema, wrapped = wire["outputSchema"], wire["wrapped"]
        # Keep profile definitions in the app-server's base config. Codex reloads
        # that config for ChatGPT workspace routing; thread-only definitions can
        # disappear during that reload in CLI 0.163.
        filesystem = {
            ":root": "deny",
            ":minimal": "read",
            str(Path(snapshot).resolve()): "read",
        }
        executable = shutil.which(self.endpoint.command[0])
        command = list(self.endpoint.command)
        if executable:
            # macOS invokes the sandbox helper through the CLI path. Both the
            # launcher and its resolved binary need read/execute access.
            filesystem[str(Path(executable).absolute())] = "read"
            filesystem[str(Path(executable).resolve())] = "read"
            command[0] = str(Path(executable).resolve())
        policy = (
            "{"
            + ", ".join(
                json.dumps(path) + ' = "read"' if access == "read" else json.dumps(path) + ' = "deny"'
                for path, access in filesystem.items()
            )
            + "}"
        )
        proc = await asyncio.create_subprocess_exec(
            *command,
            "-c",
            "permissions.polyinference_readonly.filesystem=" + policy,
            "-c",
            "permissions.polyinference_readonly.network.enabled=false",
            "-c",
            'default_permissions="polyinference_readonly"',
            cwd=str(snapshot),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            limit=1024 * 1024,
            start_new_session=True,
        )
        serial, thread_id, turn_id = 0, None, None
        event_log = NativeEventLog(self.output_cap)
        terminal, final_text, usage_event = None, None, None

        async def send(message):
            proc.stdin.write(json.dumps(message).encode() + b"\n")
            await proc.stdin.drain()

        async def receive():
            nonlocal terminal, final_text, usage_event
            line = await asyncio.wait_for(proc.stdout.readline(), self.endpoint.timeout_seconds)
            if not line:
                raise UnknownExecution("Codex app-server exited without a terminal turn")
            message = json.loads(line)
            if "method" in message:
                event_log.record(message, len(line))
                params = message.get("params") or {}
                belongs = (
                    params.get("threadId", thread_id) == thread_id
                    and (turn_id is None or params.get("turnId", turn_id) == turn_id)
                )
                # Keep execution state independently of the rolling event buffer,
                # including notifications received before turn/start's RPC reply.
                if belongs:
                    if message["method"] == "turn/completed" and (
                        turn_id is None or params.get("turn", {}).get("id") == turn_id
                    ):
                        terminal = message
                    elif message["method"] == "item/completed":
                        item = params.get("item") or {}
                        if item.get("type") == "agentMessage":
                            final_text = item.get("text")
                    elif message["method"] == "thread/tokenUsage/updated":
                        usage_event = message
                if "id" in message and message.get("method") == "item/tool/call" and callback:
                    params = message["params"]
                    if params.get("threadId") != thread_id or params.get("tool") != "polyinference_tool":
                        raise EndpointError("Native callback identity mismatch")
                    observation = await callback(params["callId"], params["arguments"])
                    await send(
                        {
                            "id": message["id"],
                            "result": {
                                "success": True,
                                "contentItems": [{"type": "inputText", "text": json.dumps(observation)}],
                            },
                        }
                    )
                elif "id" in message:
                    # Never grant native approval/escalation outside the broker.
                    await send(
                        {
                            "id": message["id"],
                            "error": {
                                "code": -32601,
                                "message": "Brokered callbacks and approvals unsupported",
                            },
                        }
                    )
            return message

        async def rpc(method, params):
            nonlocal serial
            serial += 1
            await send({"id": serial, "method": method, "params": params})
            while True:
                message = await receive()
                if message.get("id") == serial and "method" not in message:
                    if "error" in message:
                        failure = NativeJobStopped(
                            f"Codex RPC rejected {method}: {message['error'].get('code')} "
                            + str(message["error"].get("message", ""))[:1500]
                        )
                        failure.model_unavailable = model_unavailable(message["error"].get("message"),
                                                                      message["error"].get("code"))
                        raise failure
                    return message["result"]

        try:
            await rpc(
                "initialize",
                {
                    "clientInfo": {"name": "polyinference", "version": "0.1.0"},
                    "capabilities": {
                        "experimentalApi": True,
                        "optOutNotificationMethods": list(STREAMED_TEXT_METHODS),
                    },
                },
            )
            await send({"method": "initialized", "params": {}})
            params = {
                "model": self.endpoint.model,
                "cwd": str(snapshot),
                "permissions": "polyinference_readonly",
                "approvalPolicy": "never",
                "developerInstructions": wire["developerInstructions"],
                "config": {
                    "features.shell_tool": False,
                    "web_search": "disabled",
                },
            }
            if callback and not session_ref:
                params["dynamicTools"] = wire["dynamicTools"]
            if session_ref:
                params["threadId"] = session_ref
            else:
                # Model routing is owned and recorded by the OS, not an opaque provider fallback.
                params["allowProviderModelFallback"] = False
            thread = await rpc("thread/resume" if session_ref else "thread/start", params)
            sandbox = thread.get("sandbox") or {}
            if (sandbox.get("type") != "readOnly" or sandbox.get("networkAccess", False)
                    or thread.get("approvalPolicy") != "never"):
                raise NativeJobStopped("Codex did not confirm read-only permissions with escalation disabled",
                                       retryable=False)
            thread_id = thread["thread"]["id"]
            if observer:
                await observer("thread_started", thread_id, None)
            result = await rpc(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": ([{"type": "text", "text":
                        "Continue the interrupted turn from its recorded conversation. Completed host tool "
                        "operations retain their results and must not be repeated. Inspect current state through "
                        "the granted tools when needed; finish the remaining work under the original protocol."}]
                        if session_ref else wire["input"]),
                    "effort": self.endpoint.reasoning_effort,
                    "cwd": str(snapshot),
                    "approvalPolicy": "never",
                    "outputSchema": output_schema,
                },
            )
            turn_id = result["turn"]["id"]
            if observer:
                await observer("turn_started", thread_id, turn_id)
            if terminal and terminal["params"]["turn"]["id"] != turn_id:
                terminal = None
            while terminal is None:
                await receive()
            turn = terminal["params"]["turn"]
            if turn["status"] != "completed":
                failure = NativeJobStopped(
                    f"Codex turn ended: {turn['status']}: "
                    + str((turn.get("error") or {}).get("message", "No error detail"))[:1500],
                    retryable=turn["status"] not in {"cancelled", "interrupted"},
                )
                failure.model_unavailable = model_unavailable((turn.get("error") or {}).get("message"),
                                                              (turn.get("error") or {}).get("codexErrorInfo")
                                                              or (turn.get("error") or {}).get("code"))
                if turn["status"] == "failed" and failure.model_unavailable:
                    failure.native_continuation = {"session_id": thread_id, "turn_id": turn_id}
                raise failure
            if final_text is None:
                texts = [i["text"] for i in turn.get("items", []) if i.get("type") == "agentMessage"]
                final_text = texts[-1] if texts else None
            if final_text is None:
                raise NativeJobStopped("No terminal Codex agent message", output_failure=True)
            if len(final_text.encode()) > self.output_cap:
                total = ((usage_event or {}).get("params", {}).get("tokenUsage") or {}).get("total") or {}
                raise IncompleteGeneration({
                    "text": final_text.encode()[:self.output_cap].decode(errors="ignore"),
                    "usage": {**total, "total_tokens": total.get("totalTokens")},
                    "model": self.endpoint.model, "provider_id": turn_id,
                    "events": event_log.snapshot(), "event_diagnostics": event_log.diagnostics(),
                }, "native_response_byte_limit", max_output)
            if wrapped:
                try:
                    final_text = json.dumps(json.loads(final_text)["reply"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise NativeJobStopped("Terminal Codex reply has an invalid phase envelope", output_failure=True) from exc
            usage = None
            if usage_event:
                params = usage_event["params"]
                total = (params.get("tokenUsage") or {}).get("total") or {}
                if (params.get("threadId") == thread_id and params.get("turnId") == turn_id
                        and "totalTokens" in total):
                    usage = {**total, "total_tokens": total["totalTokens"]}
            return {
                "text": final_text,
                "usage": usage,
                "provider_id": turn_id,
                "session_id": thread_id,
                "model": self.endpoint.model,
                "events": event_log.snapshot(),
                "event_diagnostics": event_log.diagnostics(),
            }
        except (TimeoutError, asyncio.TimeoutError, asyncio.CancelledError) as exc:
            if thread_id and turn_id:
                try:
                    await send(
                        {
                            "id": 999999,
                            "method": "turn/interrupt",
                            "params": {"threadId": thread_id, "turnId": turn_id},
                        }
                    )
                except (BrokenPipeError, ConnectionError):
                    pass
            failure = UnknownExecution("Codex interrupted; remote termination is not established")
            failure.native_diagnostics = event_log.diagnostics()
            raise failure from exc
        except BaseException as exc:
            exc.native_diagnostics = event_log.diagnostics()
            raise
        finally:
            # Killing the local transport is not represented as remote cancellation.
            if proc.returncode is None:
                proc.terminate()
                try:
                    await asyncio.wait_for(proc.wait(), 5)
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()

    async def close(self):
        pass


class CodexProxy:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.http = HTTPInference(endpoint)

    async def generate_job(self, messages, snapshot, schema, *, max_output=4000, prepared=None):
        configured = self.endpoint.readonly_snapshot_root
        if configured is None or Path(configured).resolve() != Path(snapshot).resolve():
            raise EndpointError(
                "Proxy must be separately pinned to this read-only snapshot; no per-request cwd guarantee"
            )
        # Native tools only. No client-defined tools are sent. A successful HTTP response
        # supplies a proposal, never independent execution or completion evidence.
        result = await self.http.generate(messages, max_output, schema, prepared=prepared)
        result["events"] = [
            {
                "type": "proxy_visibility",
                "native_events": "unavailable",
                "cancellation": "unsupported",
                "workspace": str(snapshot),
            }
        ]
        return result

    async def close(self):
        await self.http.close()
