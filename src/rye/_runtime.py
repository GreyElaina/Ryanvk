from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, ChainMap, MutableMapping, MutableSequence

from rye.layout import DetailedArtifacts

if TYPE_CHECKING:
    from rye.lifespan import AsyncLifespanHostShape, LifespanHostShape

GlobalArtifacts = DetailedArtifacts()
GlobalArtifacts.protected = True

UpstreamArtifacts: ContextVar[MutableMapping[Any, Any]] = ContextVar("UpstreamArtifacts")
Layout: ContextVar[MutableSequence[DetailedArtifacts[Any, Any]]] = ContextVar("Layout")
Instances: ContextVar[MutableMapping[type, Any]] = ContextVar("Instances")
AccessStack: ContextVar[MutableMapping[Any, list[int]]] = ContextVar("AccessStack")

GlobalInstances = {}
NewInstances: ContextVar[ChainMap[type, Any]] = ContextVar("NewInstances", default=ChainMap(GlobalInstances))

LifespanHost: ContextVar[LifespanHostShape] = ContextVar("LifespanHost")
AsyncLifespanHost: ContextVar[AsyncLifespanHostShape] = ContextVar("AsyncLifespanHost")
