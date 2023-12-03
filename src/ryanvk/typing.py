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

outP = ParamSpec("outP")
outR = TypeVar("outR", covariant=True)
inP = ParamSpec("inP")
inR = TypeVar("inR", covariant=True)

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
    def collect(
        self, *args: unspecifiedCollectP.args, **kwargs: unspecifiedCollectP.kwargs
    ) -> Any:
        ...


Twin: TypeAlias = "tuple[BaseCollector, Any]"

FnComposeCollectReturnType = Generator["FnOverloadHarvest", Any, None]
FnComposeCallReturnType = Generator["FnOverloadHarvest", None, R]
