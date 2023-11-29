from __future__ import annotations
from contextvars import ContextVar
from typing import MutableMapping, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import MountpointProvider, LifespanManager

targets_artifact_map: ContextVar[MutableMapping[Any, Any]]\
    = ContextVar("targets_artifact_map")  # fmt: off


mountpoint_provider: ContextVar[MountpointProvider]\
    = ContextVar("mountpoint_provider")  # fmt: off


perform_manager: ContextVar[LifespanManager]\
    = ContextVar("perform_manager")  # fmt: off
