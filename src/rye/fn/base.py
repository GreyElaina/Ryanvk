from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Generic, Protocol, TypeVar

from rye.entity import BaseEntity
from rye.fn.compose import FnCompose
from rye.fn.entity import FnImplementEntity
from rye.operators import callee_of
from rye.typing import (
    P1,
    R1,
    FnComposeCallReturnType,
    FnComposeCollectReturnType,
    P,
    R,
    WrapCall,
    inTC,
    specifiedCollectP,
)

if TYPE_CHECKING:
    pass

K = TypeVar("K")

callShape = TypeVar("callShape", bound=Callable, covariant=True)
collectShape = TypeVar("collectShape", bound=Callable, covariant=True)


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


class Fn(Generic[collectShape, callShape], BaseEntity):
    compose_instance: FnCompose

    def __init__(self, compose_cls: type[FnCompose]):
        self.compose_instance = compose_cls(self)

    @classmethod
    def symmetric(cls: type[Fn[Callable[[inTC], Any], inTC]], entity: inTC):
        return cls(FnSymmetricCompose[inTC])

    @classmethod
    def compose(
        cls: type[Fn[collectShape, Callable[P, R]]],
        compose_cls: type[FnMethodComposeCls[collectShape, Callable[P, FnComposeCallReturnType[R]]]],
    ):
        # TODO: 考虑将其直接作为 __init__。
        return cls(compose_cls)  # type: ignore

    @classmethod
    def override(cls: type[Fn[collectShape, Callable[P, R]]], target: Fn):
        def wrapper(
            compose_cls: type[FnMethodComposeCls[collectShape, Callable[P, FnComposeCallReturnType[R]]]]
        ) -> Fn[collectShape, Callable[P, R]]:
            comp = cls.compose(compose_cls)
            comp.compose_instance.signature = target.compose_instance.signature
            return comp

        return wrapper

    @property
    def ownership(self):
        if self.collector is not None:
            return self.collector.cls

    @property
    def implements(
        self: Fn[Callable[Concatenate[inTC, specifiedCollectP], Any], Any]
    ) -> Callable[specifiedCollectP, Detour[WrapCall[..., inTC], specifiedCollectP]]:
        def wrapper(*args: specifiedCollectP.args, **kwargs: specifiedCollectP.kwargs):
            def inner(impl: Callable[Concatenate[K, P], R]):
                return FnImplementEntity(self, impl, *args, **kwargs)

            return inner

        return wrapper  # type: ignore

    @property
    def callee(self):
        return callee_of(self)
