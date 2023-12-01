from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Concatenate, Generic, Protocol, TypeVar

from ryanvk.entity import BaseEntity
from ryanvk.fn.compose import EntitiesHarvest, FnCompose
from ryanvk._runtime import _upstream_staff
from ryanvk.fn.entity import FnImplementEntity
from ryanvk.fn.record import FnRecord
from ryanvk.typing import FnComposeCallReturnType, P, R, FnComposeCollectReturnType, inP, inR, inTC, outP, outR

if TYPE_CHECKING:
    from ryanvk.staff import Staff

K = TypeVar("K")


class FnMethodComposeCls(Protocol[outP, outR, inP, inR]):
    def call(
        self, *args: outP.args, **kwargs: outP.kwargs
    ) -> FnComposeCallReturnType[outR]:
        ...

    def collect(self, *args: inP.args, **kwargs: inP.kwargs) -> FnComposeCollectReturnType:
        ...

    def entity_type(self: Any) -> inR:
        # 我不确定 self: Any 是否是必要的。
        ...


class Fn(Generic[P, R, K], BaseEntity):
    compose_instance: FnCompose

    def __init__(self, compose_cls: type[FnCompose]):
        self.compose_instance = compose_cls(self)

    # TODO: Fn.symmetric based on Compose.
    #       我严重怀疑这玩意实现不了。
    @classmethod
    def symmetric(cls, entity: Callable[Concatenate[Any, P], R]):
        class LocalCompose(Generic[outP, outR], FnCompose):
            def call(self) -> FnComposeCallReturnType[Any]:
                ...

        return cls(LocalCompose)

    @classmethod
    def compose(
        cls: type[Fn[outP, outR, Callable[inP, inR]]],
        compose_cls: type[FnMethodComposeCls[outP, outR, inP, inR]],
    ):
        return cls(compose_cls)  # type: ignore

    def implements(self: Fn[P, R, Callable[inP, inTC]], impl: inTC):
        return FnImplementEntity(self, impl)

    def call(self, staff: Staff, *args: P.args, **kwargs: P.kwargs) -> R:
        signature = self.compose_instance.signature()
        for artifacts in staff.iter_artifacts(signature):
            if signature in artifacts:
                break
        else:
            raise NotImplementedError

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
