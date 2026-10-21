"""Trusted capability registration; model callers receive only their granted ABI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import TypeAdapter

from ..contracts import Identifier, Wire
from ..primitives import canonical, digest


class WorkspaceGrant(Wire):
    workspace_id: Identifier
    process_id: Identifier
    capabilities: list[Identifier]
    check_names: list[str] = []
    expandable: bool = False


@dataclass(frozen=True)
class Capability:
    name: str
    handler: Any
    input_type: Any
    effect_class: Literal["read", "private_write", "shared_write", "external_write"]
    workspace: bool
    description: str

    @property
    def adapter(self):
        return TypeAdapter(self.input_type)

    def arguments(self, value):
        result = self.adapter.validate_python(value, strict=True)
        return result.model_dump(exclude_unset=True) if hasattr(result, "model_dump") else result

    def descriptor(self):
        return {"name": self.name, "description": self.description,
                "input_schema": self.adapter.json_schema(), "effect_class": self.effect_class,
                "workspace": self.workspace}

    @property
    def schema_digest(self):
        return digest(canonical(self.adapter.json_schema()))


class Capabilities:
    def __init__(self, records):
        self.records = records
        self.definitions = {}

    def register(self, name, handler, *, input_type=dict[str, Any], effect_class="read",
                 workspace=False, description=""):
        TypeAdapter(Identifier).validate_python(name)
        if effect_class not in {"read", "private_write", "shared_write", "external_write"}:
            raise ValueError("Unknown capability effect class")
        capability = Capability(name, handler, input_type, effect_class, workspace, description)
        existing = self.definitions.get(name)
        if existing and existing.descriptor() != capability.descriptor():
            raise ValueError("Capability already registered with another definition: " + name)
        # Pin the wire ABI, not Python function addresses, across restart.
        self.records.put_once("runtime/capability/" + name,
                              {"digest": digest(canonical(capability.descriptor()))})
        self.definitions[name] = capability
        return capability

    def get(self, name):
        if name not in self.definitions:
            raise ValueError("Unregistered capability: " + name)
        return self.definitions[name]

    def descriptors(self, names):
        return [self.get(name).descriptor() for name in names]
