from __future__ import annotations
from contextvars import ContextVar
from typing import MutableMapping, Any

targets_artifact_map: ContextVar[MutableMapping[Any, Any]]\
    = ContextVar("targets_artifact_map")  # fmt: off
