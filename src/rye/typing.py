from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    Protocol,
    TypeVar,
)

try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

try:
    from typing import TypeAlias
except ImportError:
    from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from rye.collector import BaseCollector
    from rye.fn.record import FnOverloadHarvest

T = TypeVar("T")
R = TypeVar("R", covariant=True)
R1 = TypeVar("R1", covariant=True)
P = ParamSpec("P")
P1 = ParamSpec("P1")
Q = TypeVar("Q", contravariant=True)

K = TypeVar("K", contravariant=True, bound="BaseCollector")

unspecifiedCollectP = ParamSpec("unspecifiedCollectP")
specifiedCollectP = ParamSpec("specifiedCollectP")

inRC = TypeVar("inRC", covariant=True, bound=Callable)
inTC = TypeVar("inTC", bound=Callable)


class SupportsCollect(Protocol[K, P, R]):
    def collect(self, collector: K, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class ImplementForCollect(Protocol[unspecifiedCollectP]):
    def collect(self, *args: unspecifiedCollectP.args, **kwargs: unspecifiedCollectP.kwargs) -> Any:
        ...


class WrapCall(Protocol[P, R]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class ExplictImplementShape(Protocol[inRC]):
    @property
    def implement_sample(self) -> inRC:
        ...


Twin: TypeAlias = "tuple[BaseCollector, Any]"

FnComposeCollectReturnType = Generator["FnOverloadHarvest", Any, None]
FnComposeCallReturnType = Generator["FnOverloadHarvest", None, R]
