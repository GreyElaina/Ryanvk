from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Protocol,
    TypeVar,
    runtime_checkable,
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


unspecifiedCollectP = ParamSpec("unspecifiedCollectP")
specifiedCollectP = ParamSpec("specifiedCollectP")

inRC = TypeVar("inRC", covariant=True, bound=Callable)
inQC = TypeVar("inQC", contravariant=True, bound=Callable)
inTC = TypeVar("inTC", bound=Callable)

inQ = TypeVar("inQ", contravariant=True)


class SupportsCollect(Protocol[P, R]):
    def collect(self, collector: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


@runtime_checkable
class SupportsMerge(Protocol):
    def merge(self, *records: dict):
        ...


class CallShape(Protocol[P, R]):
    def call(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class ImplementForCollect(Protocol[unspecifiedCollectP]):
    def collect(self, *args: unspecifiedCollectP.args, **kwargs: unspecifiedCollectP.kwargs) -> Any:
        ...


Twin: TypeAlias = "tuple[BaseCollector, Any]"

FnComposeCollectReturnType = Generator["FnOverloadHarvest", Any, None]
FnComposeCallReturnType = Generator["FnOverloadHarvest", None, R]
