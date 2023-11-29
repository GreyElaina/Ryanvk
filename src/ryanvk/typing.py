from __future__ import annotations

from typing import (
    Any,
    Callable,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
    runtime_checkable,
    Generator,
)
from typing_extensions import ParamSpec, TypeAlias

if TYPE_CHECKING:
    from ryanvk.collector import BaseCollector
    from ryanvk.fn.record import FnOverloadHarvest

T = TypeVar("T")
R = TypeVar("R", covariant=True)
P = ParamSpec("P")
P1 = ParamSpec("P1")

T1 = TypeVar("T1")
T2 = TypeVar("T2")

inP = ParamSpec("inP")
outP = ParamSpec("outP")
inR = TypeVar("inR", covariant=True)
outR = TypeVar("outR", covariant=True)

inRC = TypeVar("inRC", covariant=True, bound=Callable)
inTC = TypeVar("inTC", bound=Callable)


class SupportsCollect(Protocol[P, R]):
    def collect(self, collector: Any, *args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore
        ...


@runtime_checkable
class SupportsMerge(Protocol):
    def merge(self, *records: dict):
        ...


class CallShape(Protocol[P, R]):
    def call(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


Twin: TypeAlias = "tuple[BaseCollector, Any]"

FnComposeCollectReturnType = Generator[FnOverloadHarvest, Any, None]
FnComposeCallReturnType = Generator[FnOverloadHarvest, None, R]
