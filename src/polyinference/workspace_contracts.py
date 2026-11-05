"""Design-only minimal OS profile and scoped workspace extension.

Reuses the sibling 2.0 wire types. Production code should import a versioned SDK
package; the local import below only keeps these reviewable artifacts standalone.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, model_validator

from . import contracts as agent

Wire, CodeRevision, ArtifactRef = agent.Wire, agent.CodeRevision, agent.ArtifactRef
Identifier, Digest, PositiveCount, Feature = (
    agent.Identifier,
    agent.Digest,
    agent.PositiveCount,
    agent.Feature,
)


def relative_path(value: str) -> str:
    if not value or "\\" in value or ":" in value or "\x00" in value:
        raise ValueError("Use a nonempty project-relative POSIX path")
    if any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("Absolute paths and traversal are forbidden")
    if any(part.casefold() in {".git", ".polyinference"} for part in value.split("/")):
        raise ValueError("Agent file paths cannot address Git or runtime control data")
    return value


RelativePath = Annotated[str, AfterValidator(relative_path)]


class CoreProfile(Wire):
    profile_id: Identifier
    profile_version: Literal["1.0"] = "1.0"
    wire_major: Literal["2"] = "2"
    project_capacity: Literal[1] = 1
    local_model_services: Literal[1] = 1
    cloud_endpoints: Literal[1] = 1
    max_workers: PositiveCount
    local_inflight_limit: PositiveCount
    local_engine_sequence_limit: PositiveCount
    max_sequence_tokens: PositiveCount
    local_reserved_context_tokens: PositiveCount
    cloud_inflight_limit: PositiveCount
    max_pending_operations: PositiveCount
    max_tool_output_bytes: PositiveCount
    workspace_budget_bytes: PositiveCount
    host_agent_budget_bytes: PositiveCount
    shell_capacity: Literal[1] = 1
    verification_capacity: Literal[1] = 1
    routing: Literal["static_roles"] = "static_roles"
    local_admission: Literal["fifo_alternating_verifier_lane"] = "fifo_alternating_verifier_lane"
    publication: Literal["provisional_all"] = "provisional_all"
    workspace_strategy: Literal["scoped_development_full_integration"] = "scoped_development_full_integration"
    langgraph_integration: Literal["public_api_adapter"] = "public_api_adapter"
    local_backend_descriptor_ref: Identifier
    cloud_backend_descriptor_ref: Identifier
    role_backend_refs: dict[Identifier, Identifier]
    capacity_basis_ref: Identifier
    supported_features: list[Feature]

    @model_validator(mode="after")
    def feasible_static_limits(self) -> CoreProfile:
        if self.local_inflight_limit > self.local_engine_sequence_limit:
            raise ValueError("Core limits local backlog to the configured sequence cap")
        if self.local_reserved_context_tokens < self.max_sequence_tokens:
            raise ValueError("At least one maximum-size request must fit admission")
        if self.max_pending_operations < self.local_inflight_limit + self.cloud_inflight_limit:
            raise ValueError("Operation capacity must cover configured in-flight requests")
        if self.local_backend_descriptor_ref == self.cloud_backend_descriptor_ref:
            raise ValueError("Local and cloud endpoint descriptors must be distinct")
        if not {"worker", "senior"} <= self.role_backend_refs.keys():
            raise ValueError("Static maps must bind worker and senior roles")
        if any(
            reference not in {self.local_backend_descriptor_ref, self.cloud_backend_descriptor_ref}
            for reference in self.role_backend_refs.values()
        ):
            raise ValueError("Static role bindings must use the configured endpoints")
        ids = [f.feature_id for f in self.supported_features]
        if len(ids) != len(set(ids)):
            raise ValueError("Feature identifiers must be unique")
        return self


class CopiedFile(Wire):
    path: RelativePath
    copied_digest: Digest
    writable: bool


class WorkspaceManifest(Wire):
    manifest_id: Identifier
    workspace_id: Identifier
    process_id: Identifier
    task_spec_ref: Identifier
    generation: PositiveCount
    view: Literal["development", "integration"]
    materialization: Literal["scoped", "complete"]
    private_root_ref: Identifier
    original_base: CodeRevision
    captured_head: CodeRevision | None
    effective_code: CodeRevision | None
    copied_files: list[CopiedFile]
    allowed_write_paths: list[RelativePath]
    closure_basis_ref: Identifier
    preserved_delta_ref: Identifier | None

    @model_validator(mode="after")
    def view_contract(self) -> WorkspaceManifest:
        paths = [f.path for f in self.copied_files]
        if len(paths) != len(set(paths)):
            raise ValueError("A copied path has one recorded version")
        if len(self.allowed_write_paths) != len(set(self.allowed_write_paths)):
            raise ValueError("Write paths must be unique")
        if any(f.writable and f.path not in self.allowed_write_paths for f in self.copied_files):
            raise ValueError("Copied-file writable flags must stay within the declared write set")
        if self.view == "development":
            if self.materialization != "scoped" or self.captured_head is not None:
                raise ValueError("Development copies stay at their pinned base before integration")
        else:
            if (
                self.materialization != "complete"
                or self.captured_head is None
                or self.effective_code is None
            ):
                raise ValueError("Final integration requires a complete view and captured head/content")
            if self.generation < 2 or self.preserved_delta_ref is None:
                raise ValueError("Integration changes generation and preserves the task delta")
            if (
                len(
                    {
                        self.original_base.repository_id,
                        self.captured_head.repository_id,
                        self.effective_code.repository_id,
                    }
                )
                != 1
            ):
                raise ValueError("Workspace views cannot change repositories")
        return self


class ViewRequirement(Wire):
    """Required extension on each workspace-bound effect envelope."""

    workspace_id: Identifier
    manifest_ref: Identifier
    generation: PositiveCount
    view: Literal["development", "integration"]


class DeltaChange(Wire):
    action: Literal["add", "modify", "delete", "rename"]
    path: RelativePath
    source_path: RelativePath | None = None
    expected_base_digest: Digest | None
    content: ArtifactRef | None

    @model_validator(mode="after")
    def explicit_change(self) -> DeltaChange:
        if self.action == "add" and (self.content is None or self.expected_base_digest is not None):
            raise ValueError("Add names new content, not an existing base file")
        if self.action in {"modify", "delete", "rename"} and self.expected_base_digest is None:
            raise ValueError("Existing-file changes require a pinned base hash")
        if self.action == "modify" and self.content is None:
            raise ValueError("Modify needs explicit new content")
        if self.action == "delete" and self.content is not None:
            raise ValueError("Delete cannot carry replacement content")
        if self.action == "rename":
            if self.source_path is None or self.source_path == self.path:
                raise ValueError("Rename needs a distinct source path")
        elif self.source_path is not None:
            raise ValueError("Only rename uses a source path")
        return self


class WorkspaceDelta(Wire):
    delta_id: Identifier
    workspace_id: Identifier
    development_manifest_ref: Identifier
    original_base: CodeRevision
    absence_is_deletion: Literal[False] = False
    changes: list[DeltaChange]


class CoreExamples(Wire):
    profile: CoreProfile
    workspaces: list[WorkspaceManifest]
    deltas: list[WorkspaceDelta]
    view_requirements: list[ViewRequirement]
    current_manifest_refs: list[Identifier]

    @model_validator(mode="after")
    def linked_workspace_contracts(self) -> CoreExamples:
        manifests = {w.manifest_id: w for w in self.workspaces}
        if len(manifests) != len(self.workspaces):
            raise ValueError("Manifest identities must be unique")
        roots = [w.private_root_ref for w in self.workspaces]
        if len(roots) != len(set(roots)):
            raise ValueError("Each recorded writable view has a distinct private root")
        current: dict[str, WorkspaceManifest] = {}
        for reference in self.current_manifest_refs:
            manifest = manifests.get(reference)
            if manifest is None or manifest.workspace_id in current:
                raise ValueError("Each active workspace pointer selects one known manifest")
            current[manifest.workspace_id] = manifest
        for requirement in self.view_requirements:
            manifest = manifests.get(requirement.manifest_ref)
            if manifest is None:
                raise ValueError("Unknown workspace manifest")
            if (requirement.workspace_id, requirement.generation, requirement.view) != (
                manifest.workspace_id,
                manifest.generation,
                manifest.view,
            ):
                raise ValueError("A tool view requirement must identify the exact generation")
            if current.get(requirement.workspace_id) != manifest:
                raise ValueError("New dispatch cannot use a retired workspace view")
        deltas = {d.delta_id: d for d in self.deltas}
        if len(deltas) != len(self.deltas):
            raise ValueError("Delta identities must be unique")
        for delta in self.deltas:
            manifest = manifests.get(delta.development_manifest_ref)
            if manifest is None:
                raise ValueError("Unknown delta development manifest")
            if (
                manifest.view != "development"
                or manifest.original_base != delta.original_base
                or manifest.workspace_id != delta.workspace_id
            ):
                raise ValueError("A delta must preserve its own development base and workspace")
            copied = {f.path: f for f in manifest.copied_files}
            affected: set[str] = set()
            for change in delta.changes:
                endpoints = {change.path}
                if change.source_path is not None:
                    endpoints.add(change.source_path)
                if affected & endpoints or not endpoints <= set(manifest.allowed_write_paths):
                    raise ValueError("Every delta endpoint participates once and is authorized")
                affected.update(endpoints)
                if change.action in {"add", "rename"} and change.path in copied:
                    raise ValueError("Add/rename destination must not overwrite an existing base file")
                original_path = change.source_path if change.action == "rename" else change.path
                if change.action != "add":
                    original = copied.get(original_path)
                    if (
                        original is None
                        or not original.writable
                        or original.copied_digest != change.expected_base_digest
                    ):
                        raise ValueError("Existing-file delta must match a copied writable base file")
        for manifest in self.workspaces:
            if manifest.view != "integration":
                continue
            delta = deltas.get(manifest.preserved_delta_ref)
            if delta is None:
                raise ValueError("Integration must retain a known private delta")
            development = manifests[delta.development_manifest_ref]
            if (
                manifest.workspace_id,
                manifest.process_id,
                manifest.task_spec_ref,
                manifest.original_base,
            ) != (
                development.workspace_id,
                development.process_id,
                development.task_spec_ref,
                development.original_base,
            ):
                raise ValueError("Integration cannot switch the delta's workspace, owner, task or base")
            if set(manifest.allowed_write_paths) != set(development.allowed_write_paths):
                raise ValueError("Complete materialization does not expand write authority")
            if manifest.generation <= development.generation:
                raise ValueError("Integration generation must follow its development generation")
        return self
