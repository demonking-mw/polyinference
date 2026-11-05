"""Bounded SSE framing and provider completion assembly. Never exposes partial output."""

from __future__ import annotations

import codecs
import json


class StreamFault(ValueError):
    pass


class SSEDecoder:
    def __init__(self):
        self.decoder = codecs.getincrementaldecoder("utf-8-sig")("strict")
        self.buffer = ""

    def feed(self, chunk, final=False):
        self.buffer += self.decoder.decode(chunk, final=final)
        # Normalize CRLF only once both bytes arrived; a trailing CR stays buffered.
        self.buffer = self.buffer.replace("\r\n", "\n")
        if not final and self.buffer.endswith("\r"):
            self.buffer = self.buffer[:-1].replace("\r", "\n") + "\r"
        else:
            self.buffer = self.buffer.replace("\r", "\n")
        events = []
        while "\n\n" in self.buffer:
            block, self.buffer = self.buffer.split("\n\n", 1)
            data = [line[5:].lstrip(" ") for line in block.split("\n") if line.startswith("data:")]
            if data:
                events.append("\n".join(data))
        return events


class CompletionStream:
    """The adapter's wire facts; pings and lifecycle events are not token progress."""

    def __init__(self, protocol):
        self.protocol = protocol
        self.body = {}
        self.blocks = {}
        self.terminal = False
        self.finished = False
        self.error = None
        self.provider_id = None
        self.events = 0

    def accept(self, data):
        self.events += 1
        if data == "[DONE]":
            if self.protocol != "chat" or not self.finished:
                raise StreamFault("Stream ended without a completion reason")
            self.terminal = True
            return False
        item = json.loads(data)
        if not isinstance(item, dict):
            raise StreamFault("Stream event is not an object")
        kind = item.get("type")
        progress = False
        if kind == "error" or item.get("error"):
            self.error = item.get("error") or {}
            self.terminal = True
            return False
        if self.protocol == "anthropic":
            if kind == "message_start":
                self.body = dict(item["message"])
                self.provider_id = self.body.get("id")
            elif kind == "content_block_start":
                block = item["content_block"]
                # Retain block type for completion validation, never hidden reasoning.
                self.blocks[item["index"]] = {"type": block["type"],
                    **({"text": block.get("text", "")} if block["type"] == "text" else {})}
                progress = bool(block.get("text") or block.get("thinking"))
            elif kind == "content_block_delta":
                delta = item["delta"]
                progress = bool(delta.get("text") or delta.get("thinking") or delta.get("partial_json"))
                if delta.get("type") == "text_delta":
                    self.blocks[item["index"]]["text"] += delta["text"]
            elif kind == "message_delta":
                self.body.update(item.get("delta") or {})
                self.body["usage"] = {**self.body.get("usage", {}), **item.get("usage", {})}
            elif kind == "message_stop":
                self.body["content"] = [self.blocks[i] for i in sorted(self.blocks)]
                if not self.body.get("stop_reason"):
                    raise StreamFault("Message stop is missing a completion reason")
                self.terminal = True
        elif self.protocol == "chat":
            for key in ("id", "model", "usage"):
                if item.get(key) is not None:
                    self.body[key] = item[key]
            self.provider_id = self.body.get("id")
            choices = item.get("choices") or []
            for choice in choices:
                if choice.get("index", 0) != 0:
                    raise StreamFault("Multiple streamed choices are unsupported")
                delta = choice.get("delta") or {}
                progress = progress or bool(delta.get("content") or delta.get("reasoning_content"))
                target = self.body.setdefault("choices", [{"message": {"content": ""}, "finish_reason": None}])[0]
                if delta.get("content"):
                    target["message"]["content"] += delta["content"]
                if delta.get("tool_calls") or delta.get("function_call"):
                    target["message"]["tool_calls"] = [True]
                if choice.get("finish_reason"):
                    self.finished = True
                    target["finish_reason"] = choice["finish_reason"]
        elif self.protocol == "responses":
            response = item.get("response") or {}
            if response.get("id"):
                self.provider_id = response["id"]
            progress = kind in {"response.output_text.delta", "response.reasoning_text.delta",
                                "response.reasoning_summary_text.delta"} and bool(item.get("delta"))
            if kind in {"response.completed", "response.incomplete", "response.failed"}:
                self.body = response
                self.terminal = True
        else:
            raise StreamFault("Unsupported streaming protocol")
        return progress
