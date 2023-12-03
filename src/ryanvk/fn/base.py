from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Generic, Protocol, TypeVar

from ryanvk.entity import BaseEntity
from ryanvk.fn.compose import EntitiesHarvest, FnCompose
from ryanvk._runtime import _upstream_staff
from ryanvk.fn.entity import FnImplementEntity
from ryanvk.fn.record import FnRecord
from ryanvk.typing import (
    FnComposeCallReturnType,
    P,
    R,
    FnComposeCollectReturnType,
    outP,
    outR,
    inP,
    inR,
    inTC,
    specifiedCollectP,
    unspecifiedCollectP,
)

if TYPE_CHECKING:
    from ryanvk.staff import Staff

K = TypeVar("K")

outboundShape = TypeVar("outboundShape", bound=Callable, covariant=True)


class FnMethodComposeCls(Protocol[outP, outR, unspecifiedCollectP]):
    def call(
        self, *args: outP.args, **kwargs: outP.kwargs
    ) -> FnComposeCallReturnType[outR]:
        ...

    def collect(
        self,
        *args: unspecifiedCollectP.args,
        **kwargs: unspecifiedCollectP.kwargs,
    ) -> FnComposeCollectReturnType:
        ...


class Fn(Generic[unspecifiedCollectP, outboundShape], BaseEntity):
    compose_instance: FnCompose

    def __init__(self, compose_cls: type[FnCompose]):
        self.compose_instance = compose_cls(self)

    # TODO: Fn.symmetric based on Compose.
    #       我严重怀疑这玩意实现不了。
    @classmethod
    def symmetric(cls, entity: Callable[Concatenate[Any, P], R]):
        class LocalCompose(Generic[outP, outR], FnCompose):
            def call(
                self, *args: outP.args, **kwargs: outP.kwargs
            ) -> FnComposeCallReturnType[outR]:
                with self.harvest() as entities:
                    yield self.singleton.call(None)

                return entities.first(*args, **kwargs)

        return cls(LocalCompose)

    @classmethod
    def compose(
        cls: type[Fn[unspecifiedCollectP, Callable[outP, outR]]],
        compose_cls: type[FnMethodComposeCls[outP, outR, unspecifiedCollectP]],
    ):
        return cls(compose_cls)  # type: ignore

    @property
    def implements(
        self: Fn[Concatenate[Callable[inP, inR], specifiedCollectP], Any]
    ) -> Callable[
        specifiedCollectP,
        Callable[
            [Callable[Concatenate[K, inP], inR]],
            FnImplementEntity[Callable[Concatenate[K, inP], inR], specifiedCollectP],
        ],
    ]:
        def wrapper(*args: specifiedCollectP.args, **kwargs: specifiedCollectP.kwargs):
            def inner(
                impl: Callable[Concatenate[K, inP], inR]
            ) -> FnImplementEntity[
                Callable[Concatenate[K, inP], inR], specifiedCollectP
            ]:
                return FnImplementEntity(self, impl, *args, **kwargs)

            return inner

        return wrapper  # type: ignore

    def call1(self: Fn[..., inTC], staff: Staff) -> inTC:
        def wrapper(*args, **kwargs):
            return self.call(staff, *args, **kwargs)

        return wrapper  # type: ignore

    def call(
        self: Fn[..., Callable[P, R]], staff: Staff, *args: P.args, **kwargs: P.kwargs
    ) -> R:
        # FIXME: 什么时候去给 pyright 提个 issue 让 eric 彻底重构下现在 TypeVar binding 这坨狗屎。
        #
        #        无法将“type[str]”类型的参数分配给函数“call”中类型为“type[T@call]”的参数“value”
        #            无法将类型“type[str]”分配给类型“type[T@call]”
        #
        #        真是畜生啊。

        signature = self.compose_instance.signature()
        for artifacts in staff.iter_artifacts(signature):
            if signature in artifacts:
                record: FnRecord = artifacts[signature]
                define = record["define"]

                token = _upstream_staff.set(staff)
                try:
                    iters = define.compose_instance.call(*args, **kwargs)
                    harvest_info = next(iters)
                    harv = EntitiesHarvest.mutation_endpoint.get()
                    while True:
                        scope = record["overload_scopes"][harvest_info.name]
                        stage = harvest_info.overload.harvest(scope, harvest_info.value)
                        harv.commit(stage)
                        harvest_info = next(iters)

                except StopIteration as e:
                    return e.value
                finally:
                    _upstream_staff.reset(token)
        else:
            raise NotImplementedError
