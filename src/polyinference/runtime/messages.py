"""Durable, plain-text user notifications for any hosted agent."""

from __future__ import annotations

from pydantic import Field, field_validator

from ..contracts import Wire
from ..primitives import now


class UserNotification(Wire):
    text: str = Field(min_length=1, max_length=16000)

    @field_validator("text")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("User notification must contain text")
        return value


class Messages:
    def __init__(self, records):
        self.records = records

    async def notify(self, request, arguments):
        key = "user-message/" + request.operation_id
        value = {
            "text": arguments["text"],
            "scope": request.scope.model_dump(mode="json"),
        }
        retained = self.records.get(key)
        if retained:
            if any(retained[1][field] != content for field, content in value.items()):
                raise ValueError("User notification identity reused with different content")
            return {"message_ref": key}
        value["created_at"] = now().isoformat()
        self.records.put_once(key, value)
        # Preserve complete multiline messages, excluding terminal controls.
        text = "".join(c for c in value["text"] if c.isprintable() or c in "\n\t")
        try:
            print(f"[{value['scope']['process_id']}] {text}", flush=True)
        except (OSError, UnicodeError, ValueError):
            pass  # A closed terminal must not undo a durable notification.
        return {"message_ref": key}
