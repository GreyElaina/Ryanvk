from __future__ import annotations

from contextvars import ContextVar
from typing import Any, MutableMapping, MutableSequence

ArtifactDest: ContextVar[MutableMapping[Any, Any]]\
    = ContextVar("ArtifactDest")  # fmt: off

GlobalArtifacts: MutableMapping[Any, Any] = {}
# FIXME: immutable by default, mutable partially.

Layout: ContextVar[MutableSequence[MutableMapping[Any, Any]]] = ContextVar("Layout")
Instances: ContextVar[MutableMapping[type, Any]] = ContextVar("Instances")
AccessStack: ContextVar[MutableMapping[Any, list[int]]] = ContextVar("AccessStack")
