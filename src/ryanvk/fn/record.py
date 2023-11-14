from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Callable, TypedDict

if TYPE_CHECKING:
    from ryanvk.collector import BaseCollector
    from ryanvk.fn.overload import FnOverload
    from .base import Fn


class FnRecord(TypedDict):
    define: Fn
    overload_enabled: bool
    overload_scopes: dict[str, dict[Any, Any]]
    legecy_slot: tuple[BaseCollector, Callable] | None


@dataclass(eq=True, frozen=True)
class FnImplement:
    fn: Fn

    # TODO: new merge


@dataclass(eq=True, frozen=True)
class FnOverloadHarvest:
    name: str
    overload: FnOverload
    value: Any
