from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, MutableMapping, MutableSequence

if TYPE_CHECKING:
    from .manager import LifespanManager, MountpointProvider

targets_artifact_map: ContextVar[MutableMapping[Any, Any]]\
    = ContextVar("targets_artifact_map")  # fmt: off


mountpoint_provider: ContextVar[MountpointProvider]\
    = ContextVar("mountpoint_provider")  # fmt: off


perform_manager: ContextVar[LifespanManager]\
    = ContextVar("perform_manager")  # fmt: off


# --- Ryanvk v1.3 ---

GlobalArtifacts: MutableMapping[Any, Any] = {}
# FIXME: immutable by default, mutable partially.

Layout: ContextVar[MutableSequence[MutableMapping[Any, Any]]] = ContextVar("Layout")
Instances: ContextVar[MutableMapping[type, Any]] = ContextVar("Instances")
AccessStack: ContextVar[MutableMapping[Any, list[int]]] = ContextVar("AccessStack")
