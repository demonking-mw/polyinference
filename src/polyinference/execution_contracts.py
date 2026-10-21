"""Optional command-resource definitions; selection and acceptance are application policy."""

from typing import Annotated

from pydantic import Field

from .contracts import Wire
from .workspace_contracts import RelativePath


class Check(Wire):
    name: str
    argv: Annotated[list[str], Field(min_length=1)]
    timeout_seconds: Annotated[float, Field(gt=0, le=600)] = 60
    output_paths: list[RelativePath] = Field(default_factory=list)
