from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    Generator,
    Generic,
    overload,
)

from rye.fn.record import FnImplement
from rye.operator.artifacts import iter_artifacts
from rye.typing import R1, P, Q, R, inTC

if TYPE_CHECKING:
    from rye._capability import CapabilityPerform
    from rye.fn import Fn
    from rye.fn.record import FnRecord
    from rye.perform import BasePerform


class _WrapGenerator(Generic[R, Q, R1]):
    value: R1

    def __init__(self, gen: Generator[R, Q, R1]):
        self.gen = gen

    def __iter__(self) -> Generator[R, Q, R1]:
        self.value = yield from self.gen
        return self.value


def callee_of(target: Fn[Any, inTC] | FnImplement) -> inTC:
    from rye.fn import Fn
    from rye.fn.compose import EntitiesHarvest

    def wrapper(*args, **kwargs) -> Any:
        if isinstance(target, Fn):
            signature = target.compose_instance.signature()
        else:
            signature = target

        for artifacts in iter_artifacts(signature):
            if signature in artifacts:
                record: FnRecord = artifacts[signature]
                define = record["define"]

                wrap = _WrapGenerator(define.compose_instance.call(*args, **kwargs))

                for harvest_info in wrap:
                    scope = record["overload_scopes"][harvest_info.name]
                    stage = harvest_info.overload.harvest(scope, harvest_info.value)
                    endpoint = EntitiesHarvest.mutation_endpoint.get(None)
                    if endpoint is not None:
                        endpoint.commit(stage)

                return wrap.value
        else:
            raise NotImplementedError

    return wrapper  # type: ignore


@overload
def is_implemented(perform: type[BasePerform] | BasePerform, target: type[CapabilityPerform]) -> bool:
    ...


@overload
def is_implemented(perform: type[BasePerform] | BasePerform, target: Fn) -> bool:
    ...


@overload
def is_implemented(
    perform: type[BasePerform] | BasePerform,
    target: Fn[Callable[Concatenate[Any, P], Any], Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> bool:
    ...


def is_implemented(
    perform: type[BasePerform] | BasePerform, target: type[CapabilityPerform] | Fn, *args, **kwargs
) -> bool:
    if not isinstance(perform, type):
        perform = perform.__class__

    if isinstance(target, type):
        for define in target.__collector__.definations:
            if define.compose_instance.signature() in perform.__collector__.artifacts:
                return True
    else:
        fn_sign = target.compose_instance.signature()
        pred = fn_sign in perform.__collector__.artifacts

        if not pred:
            return False

        if not (args or kwargs):
            return True

        record: FnRecord = perform.__collector__.artifacts[fn_sign]
        overload_scopes = record["overload_scopes"]

        slots = []

        for harvest_info in target.compose_instance.collect(Any, *args, **kwargs):
            sign = harvest_info.overload.digest(harvest_info.value)
            if harvest_info.name not in overload_scopes:
                return False
            scope = overload_scopes[harvest_info.name]
            twin_slot = harvest_info.overload.access(scope, sign)
            if twin_slot is None:
                return False
            slots.append(twin_slot)

        if slots and set(slots.pop()).intersection(*slots):
            return True

    return False
