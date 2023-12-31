from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Generator,
    Generic,
    Protocol,
    TypeVar,
)

from typing_extensions import ParamSpec, TypeAlias

if TYPE_CHECKING:
    from ryanvk.collector import BaseCollector
    from ryanvk.fn.record import FnOverloadHarvest

T = TypeVar("T")
R = TypeVar("R", covariant=True)
R1 = TypeVar("R1", covariant=True)
P = ParamSpec("P")
P1 = ParamSpec("P1")
Q = TypeVar("Q", contravariant=True)

unspecifiedCollectP = ParamSpec("unspecifiedCollectP")
specifiedCollectP = ParamSpec("specifiedCollectP")

inRC = TypeVar("inRC", covariant=True, bound=Callable)
inTC = TypeVar("inTC", bound=Callable)


class SupportsCollect(Protocol[P, R]):
    def collect(self, collector: Any, *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class ImplementForCollect(Protocol[inRC]):
    @property
    def collect(self) -> inRC:
        ...

class WrapCall(Protocol[P, R]):
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        ...

class AsCall(Protocol[R]):
    def __call__(self: AsCall[Callable[P, R1]], *args: P.args, **kwds: P.kwargs) -> R1:
        ...
        
class Detour1(Protocol[R1]):
    def __call__(self: Detour1[Callable[P, Any]]) -> Callable[P, Any]:
        ...

class DbgSlot(Generic[R]):
    # NOTE: R => Callable[[], inTC] -> inTC 会因为无法对 inTC 进行 overload-transform 导致崩溃。
    # NOTE:
    def test(self: DbgSlot[Callable[[], inTC]]) -> DbgSlot[inTC]:
        ...

    # NOTE: 这样无法将 TypeVar 转换为可用的，而之前的处理办法是 `Fn[callShape]` (Fn.call)，很显然，不太能直接套用到此例中。
    # NOTE: 毕竟如果这个 made it works 了，那么之前 Fn.call 就能修的能用了。
    # NOTE: 要不丢 TypeVar mapping，要不崩 pyright，选一个吧（笑）
    #       我都不选。
    def test1(self: DbgSlot[inTC]) -> inTC:
        ...

    def __call__(self: DbgSlot[Callable[P, R1]], *args: P.args, **kwargs: P.kwargs) -> R1:
        ...


Twin: TypeAlias = "tuple[BaseCollector, Any]"

FnComposeCollectReturnType = Generator["FnOverloadHarvest", Any, None]
FnComposeCallReturnType = Generator["FnOverloadHarvest", None, R]
