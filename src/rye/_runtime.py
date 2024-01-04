from __future__ import annotations

from contextvars import ContextVar
from typing import Any, MutableMapping, MutableSequence

GlobalArtifacts: MutableMapping[Any, Any] = {}

ArtifactDest: ContextVar[MutableMapping[Any, Any]] = ContextVar("ArtifactDest")
# FIXME: immutable by default, mutable partially.

Layout: ContextVar[MutableSequence[MutableMapping[Any, Any]]] = ContextVar("Layout")
Instances: ContextVar[MutableMapping[type, Any]] = ContextVar("Instances")
AccessStack: ContextVar[MutableMapping[Any, list[int]]] = ContextVar("AccessStack")
