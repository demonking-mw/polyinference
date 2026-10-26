"""Arguments of optional filesystem and foreground-command capabilities."""

from __future__ import annotations

from pydantic import Field

from ..contracts import Wire
from ..workspace_contracts import RelativePath


class FileList(Wire):
    offset: int | None = None
    limit: int | None = None


class FileRead(FileList):
    path: RelativePath
    max_bytes: int | None = Field(default=None, ge=1)


class FileSearch(Wire):
    pattern: str


class FileDelete(Wire):
    path: RelativePath
    expected_digest: str | None


class FileWrite(FileDelete):
    content: str


class FilePatch(FileDelete):
    old_text: str
    new_text: str


class CheckRun(Wire):
    name: str


class ShellRun(Wire):
    script: str
    cwd: str | None = None
    timeout_seconds: float | None = Field(default=None, gt=0, le=600)


class SelectBranch(Wire):
    name: str
    create: bool | None = False


FILE_CAPABILITIES = {
    "files.list": (FileList, "read"), "files.read": (FileRead, "read"),
    "files.search": (FileSearch, "read"), "files.delete": (FileDelete, "private_write"),
    "files.write": (FileWrite, "private_write"), "files.patch": (FilePatch, "private_write"),
    "checks.run": (CheckRun, "private_write"), "shell.run": (ShellRun, "private_write"),
    "repository.select_branch": (SelectBranch, "private_write"),
}
