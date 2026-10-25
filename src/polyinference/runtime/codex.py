"""Codex native senior and brokered coding-phase jobs.

Native events remain observations. Each phase starts a fresh native thread;
only actual dynamic-tool callbacks execute host capabilities.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from .inference import EndpointError, HTTPInference, UnknownExecution

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


class CodexAppServer:
    def __init__(self, endpoint):
        self.endpoint = endpoint

    async def generate_job(self, messages, snapshot, schema, callback=None):
        output_schema, wrapped = strict_output_schema(schema)
        if wrapped:
            messages = [
                *messages,
                {
                    "role": "user",
                    "content": 'Return the final phase JSON inside {"reply": ...}, as required by the output schema.',
                },
            ]
        # Keep profile definitions in the app-server's base config. Codex reloads
        # that config for ChatGPT workspace routing; thread-only definitions can
        # disappear during that reload in CLI 0.163.
        filesystem = {
            ":root": "deny",
            ":minimal": "read",
            str(Path(snapshot).resolve()): "read",
        }
        policy = (
            "{"
            + ", ".join(
                json.dumps(path) + ' = "read"' if access == "read" else json.dumps(path) + ' = "deny"'
                for path, access in filesystem.items()
            )
            + "}"
        )
        proc = await asyncio.create_subprocess_exec(
            *self.endpoint.command,
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
        serial, events, thread_id, turn_id = 0, [], None, None

        async def send(message):
            proc.stdin.write(json.dumps(message).encode() + b"\n")
            await proc.stdin.drain()

        async def receive():
            line = await asyncio.wait_for(proc.stdout.readline(), self.endpoint.timeout_seconds)
            if not line:
                raise UnknownExecution("Codex app-server exited without a terminal turn")
            message = json.loads(line)
            if "method" in message:
                # Also filter locally for older servers that ignore opt-out.
                # Requests must still be retained and answered through the broker.
                if "id" in message or message["method"] not in STREAMED_TEXT_METHODS:
                    if len(events) >= 2000:
                        raise UnknownExecution("Native event limit exceeded")
                    events.append(message)
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
                        raise NativeJobStopped(
                            f"Codex RPC rejected {method}: {message['error'].get('code')} "
                            + str(message["error"].get("message", ""))[:1500]
                        )
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
                "config": {
                    "features.shell_tool": False,
                    "web_search": "disabled",
                },
            }
            if callback:
                params["dynamicTools"] = [
                    {
                        "type": "function",
                        "name": "polyinference_tool",
                        "description": "Execute a scoped host file, shell, branch or check tool. Use for all effects.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "tool": {
                                    "type": "string",
                                    "enum": [
                                        "files.list",
                                        "files.read",
                                        "files.write",
                                        "files.delete",
                                        "checks.run",
                                        "shell.run",
                                        "repository.select_branch",
                                    ],
                                },
                                "arguments": {
                                    "type": "object",
                                    "properties": {
                                        **{
                                            name: {"type": ["string", "null"]}
                                            for name in (
                                                "path",
                                                "content",
                                                "expected_digest",
                                                "name",
                                                "script",
                                                "cwd",
                                            )
                                        },
                                        "timeout_seconds": {"type": ["integer", "null"]},
                                        "create": {"type": ["boolean", "null"]},
                                    },
                                    "required": [
                                        "path",
                                        "content",
                                        "expected_digest",
                                        "name",
                                        "script",
                                        "cwd",
                                        "timeout_seconds",
                                        "create",
                                    ],
                                    "additionalProperties": False,
                                    "description": "Supply fields for the chosen tool; use null for unused fields.",
                                },
                            },
                            "required": ["tool", "arguments"],
                            "additionalProperties": False,
                        },
                    }
                ]
                messages = [
                    *messages,
                    {
                        "role": "user",
                        "content": "Execute actions internally using polyinference_tool. Do not return an action as your "
                        "final answer. Finish this phase with candidate, assessment or needs_review. "
                        "The host owns all phase changes and publication.",
                    },
                ]
            thread = await rpc("thread/start", params)
            thread_id = thread["thread"]["id"]
            result = await rpc(
                "turn/start",
                {
                    "threadId": thread_id,
                    "input": [{"type": "text", "text": json.dumps(messages)}],
                    "cwd": str(snapshot),
                    "approvalPolicy": "never",
                    "outputSchema": output_schema,
                },
            )
            turn_id = result["turn"]["id"]
            # Events can arrive before the start response; inspect retained events first.
            terminal = next(
                (
                    e
                    for e in events
                    if e.get("method") == "turn/completed"
                    and e.get("params", {}).get("turn", {}).get("id") == turn_id
                ),
                None,
            )
            while terminal is None:
                message = await receive()
                if (
                    message.get("method") == "turn/completed"
                    and message.get("params", {}).get("turn", {}).get("id") == turn_id
                ):
                    terminal = message
            turn = terminal["params"]["turn"]
            if turn["status"] != "completed":
                raise NativeJobStopped(
                    f"Codex turn ended: {turn['status']}: "
                    + str((turn.get("error") or {}).get("message", "No error detail"))[:1500]
                )
            texts = [
                e["params"]["item"]["text"]
                for e in events
                if e.get("method") == "item/completed"
                and e.get("params", {}).get("item", {}).get("type") == "agentMessage"
            ]
            if not texts:
                texts = [i["text"] for i in turn.get("items", []) if i.get("type") == "agentMessage"]
            if not texts:
                raise NativeJobStopped("No terminal Codex agent message")
            final_text = texts[-1]
            if wrapped:
                try:
                    final_text = json.dumps(json.loads(final_text)["reply"])
                except (ValueError, KeyError, TypeError) as exc:
                    raise NativeJobStopped("Terminal Codex reply has an invalid phase envelope") from exc
            token_updates = [
                e["params"]["tokenUsage"]["total"]
                for e in events
                if e.get("method") == "thread/tokenUsage/updated"
                and e.get("params", {}).get("threadId") == thread_id
                and e.get("params", {}).get("turnId") == turn_id
                and "totalTokens" in e.get("params", {}).get("tokenUsage", {}).get("total", {})
            ]
            usage = (
                {**token_updates[-1], "total_tokens": token_updates[-1]["totalTokens"]}
                if token_updates
                else None
            )
            return {
                "text": final_text,
                "usage": usage,
                "provider_id": turn_id,
                "session_id": thread_id,
                "model": self.endpoint.model,
                "events": events,
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
            raise UnknownExecution("Codex interrupted; remote termination is not established") from exc
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

    async def generate_job(self, messages, snapshot, schema):
        configured = self.endpoint.readonly_snapshot_root
        if configured is None or Path(configured).resolve() != Path(snapshot).resolve():
            raise EndpointError(
                "Proxy must be separately pinned to this read-only snapshot; no per-request cwd guarantee"
            )
        # Native tools only. No client-defined tools are sent. A successful HTTP response
        # supplies a proposal, never independent execution or completion evidence.
        result = await self.http.generate(messages, 4000, schema)
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
