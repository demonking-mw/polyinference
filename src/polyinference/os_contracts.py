"""Additive OS records; the historical wire 2.0 publication types stay intact."""

from typing import Literal

from .contracts import CodeRevision, Identifier, Record, TaskReport


class PrivateTaskReport(TaskReport):
    """A normally assessed failure retained without shared-head publication."""

    verdict: Literal["fail"] = "fail"
    publication_policy: Literal["retain_failed"] = "retain_failed"
    code_location: Literal["private"] = "private"


class PrivateCommitReceipt(Record):
    kind: Literal["private_commit_receipt"] = "private_commit_receipt"
    publication_operation_id: Identifier
    report_ref: Identifier
    previous_head: CodeRevision
    candidate: CodeRevision
    verification_permit_ref: Identifier
    publication_policy: Literal["retain_failed"] = "retain_failed"


def task_report(value):
    cls = PrivateTaskReport if value.get("code_location") == "private" else TaskReport
    return cls.model_validate(value)
