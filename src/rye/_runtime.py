from __future__ import annotations

from contextvars import ContextVar
from typing import Any, MutableMapping, MutableSequence

from rye.layout import DetailedArtifacts

GlobalArtifacts = DetailedArtifacts()
GlobalArtifacts.protected = True

UpstreamArtifacts: ContextVar[MutableMapping[Any, Any]] = ContextVar("UpstreamArtifacts")
Layout: ContextVar[MutableSequence[DetailedArtifacts[Any, Any]]] = ContextVar("Layout")
Instances: ContextVar[MutableMapping[type, Any]] = ContextVar("Instances")
AccessStack: ContextVar[MutableMapping[Any, list[int]]] = ContextVar("AccessStack")
