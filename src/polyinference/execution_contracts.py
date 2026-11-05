"""Optional command-resource definitions; selection and acceptance are application policy."""

from typing import Annotated

from pydantic import Field

from .contracts import Wire
from .os_config import BOUNDS, CHECK_DEFAULT_SECONDS
from .workspace_contracts import RelativePath


class Check(Wire):
    name: str
    argv: Annotated[list[str], Field(min_length=1)]
    timeout_seconds: Annotated[float, Field(gt=0, le=BOUNDS["check_seconds"])] = Field(default=CHECK_DEFAULT_SECONDS, validate_default=True)
    output_paths: list[RelativePath] = Field(default_factory=list)
    required_paths: list[RelativePath] = Field(default_factory=list, exclude_if=lambda value: not value)
