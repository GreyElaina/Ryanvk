from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Protocol, TypeVar, Generic, Any

from ryanvk.entity import BaseEntity
from ryanvk.fn.compose import FnCompose, _StaffCtx
from ryanvk.fn.entity import FnImplementEntity
from ryanvk.fn.record import FnRecord
from ryanvk.typing import P, R, inP, outP, inR, outR, FnComposeCallReturnType, inTC

if TYPE_CHECKING:
    from ryanvk.staff import Staff

K = TypeVar("K")


class FnMethodComposeCls(
    Protocol[
        outP,
        outR,
        inP,
        inR,
    ]
):
    def call(
        self, *args: outP.args, **kwargs: outP.kwargs
    ) -> FnComposeCallReturnType[outR]:
        ...

    def collect(self, *args: inP.args, **kwargs: inP.kwargs):
        ...

    def entity_type(self: Any) -> inR:
        # 我不确定 self: Any 是否是必要的。
        ...


class Fn(Generic[P, R, K], BaseEntity):
    compose_instance: FnCompose

    def __init__(self, compose_cls: type[FnCompose]):
        self.compose_instance = compose_cls(self)

    """
    # TODO: Fn.symmetric based on Compose.
    @classmethod
    def symmetric(cls, entity: Callable[Concatenate[Any, P], R]):
        return cls()
    """

    @classmethod
    def compose(
        cls: type[Fn[outP, outR, Callable[inP, inR]]],
        compose_cls: type[FnMethodComposeCls[outP, outR, inP, inR]],
    ):
        return cls(compose_cls)  # type: ignore

    # 重写为 Fn.implements，在 FnImplementEntity 里。

    def implements(self: Fn[P, R, Callable[inP, inTC]], impl: inTC):
        return FnImplementEntity(self, impl)

    def call(self, staff: Staff, *args: P.args, **kwargs: P.kwargs) -> R:
        signature = self.compose_instance.signature()
        for artifacts in staff.iter_artifacts():
            if signature in artifacts:
                break
        else:
            raise NotImplementedError

        record: FnRecord = artifacts[signature]
        define = record["define"]

        if not record["overload_enabled"]:
            assert record["legecy_slot"] is not None
            collector, entity = record["legecy_slot"]
            instance = staff.instances[collector.cls]  # TODO: new instance maintain
            return entity(instance, *args, **kwargs)

        token = _StaffCtx.set(staff)
        try:
            iters = define.compose_instance.call(*args, **kwargs)

            harvest = next(iters)
            while True:
                scope = record["overload_scopes"][harvest.name]
                overload_ = harvest.overload
                overload_sign = overload_.signature_from_call_value(harvest.value)
                harvest = iters.send(overload_.harvest(scope, overload_sign))

        except StopIteration as e:
            return e.value
        finally:
            _StaffCtx.reset(token)
