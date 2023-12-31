from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Generic, Protocol, Self, TypeVar, overload

from ryanvk.collector import BaseCollector
from ryanvk.entity import BaseEntity, EntityAssignInfo
from ryanvk.fn.compose import EntitiesHarvest, FnCompose
from ryanvk.fn.entity import FnImplementEntity
from ryanvk.fn.record import FnRecord
from ryanvk.ops import callee_of
from ryanvk.typing import (
    FnComposeCallReturnType,
    FnComposeCollectReturnType,
    P,
    P1,
    R,
    R1,
    WrapCall,
    inTC,
    inRC,
    T,
    specifiedCollectP,
    unspecifiedCollectP,
)

if TYPE_CHECKING:
    from ryanvk.perform import BasePerform

K = TypeVar("K")

callShape = TypeVar("callShape", bound=Callable, covariant=True)
collectShape = TypeVar("collectShape", bound=Callable, covariant=True)

outboundShape = TypeVar("outboundShape", bound=Callable, covariant=True)


class FnMethodComposeCls(Protocol[collectShape, callShape]):
    @property
    def collect(self) -> collectShape:
        ...

    @property
    def call(self) -> callShape:
        ...


class FnSymmetricCompose(Generic[inTC], FnCompose):
    def call(self: FnSymmetricCompose[Callable[P, R]], *args: P.args, **kwargs: P.kwargs) -> FnComposeCallReturnType[R]:
        with self.harvest() as entities:
            yield self.singleton.call(None)

        return entities.first(*args, **kwargs)

    def collect(self, implement: inTC) -> FnComposeCollectReturnType:
        yield self.singleton.collect(None)

class Detour(Protocol[R, specifiedCollectP]):
    def __call__(
        self: Detour[WrapCall[..., Callable[P1, R1]], specifiedCollectP], implement: Callable[Concatenate[K, P1], R1]
    ) -> FnImplementEntity[Callable[Concatenate[K, P1], R1], specifiedCollectP]:
        ...

class DetourPlus(Protocol[inRC]):
    def __call__(self: DetourPlus[Callable[Concatenate[Any, P], R]], implement: Callable[P, R]):
        ...

class DetourPlus1(Protocol[inRC]):
    def __call__(self: DetourPlus1[Callable[Concatenate[Any, P], R]], *args: P.args, **kwargs: P.kwargs) -> R:
        ...


class Fn(Generic[collectShape, callShape], BaseEntity):
    compose_instance: FnCompose

    def __init__(self, compose_cls: type[FnCompose]):
        self.compose_instance = compose_cls(self)

    @classmethod
    def symmetric(
        cls: type[Fn[DetourPlus[inTC], DetourPlus1[inTC]]], entity: inTC
    ):
        # 有个问题：这里必须拆 Callable，然后拆就会丢 TypeVar bindings.
        # 难崩，看看能不能 Protocol.__call__ + self-casting 解决。
        return cls(FnSymmetricCompose[inTC])

    @classmethod
    def compose(
        cls: type[Fn[collectShape, Callable[P, R]]],
        compose_cls: type[FnMethodComposeCls[collectShape, Callable[P, FnComposeCallReturnType[R]]]],
    ):
        # TODO: 考虑将其直接作为 __init__。
        return cls(compose_cls)  # type: ignore

    @property
    def ownership(self):
        if self.collector is not None:
            return self.collector.cls

    @property
    def implements(
        self: Fn[Callable[Concatenate[T, specifiedCollectP], Any], Any]
    ) -> Callable[specifiedCollectP, Detour[WrapCall[..., T], specifiedCollectP]]:
        def wrapper(*args: specifiedCollectP.args, **kwargs: specifiedCollectP.kwargs):
            def inner(impl: Callable[Concatenate[K, P], R]):
                return FnImplementEntity(self, impl, *args, **kwargs)

            return inner

        return wrapper  # type: ignore

    @property
    def callee(self):
        return callee_of(self)

    # TODO: check for completed implementations
