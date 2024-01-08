from __future__ import annotations

from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    ContextManager,
    Generator,
    Generic,
    Literal,
    MutableMapping,
    MutableSequence,
    overload,
)

from rye.fn.record import FnImplement
from rye.layout import DetailedArtifacts

from ._runtime import AccessStack, GlobalArtifacts, Instances, Layout
from .typing import R1, P, Q, R, inTC
from .utilities import standalone_context

if TYPE_CHECKING:
    from ._capability import CapabilityPerform
    from .fn import Fn
    from .fn.record import FnRecord
    from .perform import BasePerform


def layout() -> MutableSequence[DetailedArtifacts[Any, Any]]:
    return Layout.get(None) or [GlobalArtifacts]


def shallow():
    return layout()[0]


@contextmanager
def isolate(
    *collections: MutableMapping[Any, Any] | DetailedArtifacts,
    default_protected: bool = True,
    inherits: bool = True,
):
    colls = [*collections]

    for index, value in enumerate(colls):
        if not isinstance(value, DetailedArtifacts):
            v = DetailedArtifacts(value)
            v.protected = default_protected
            colls[index] = v
            
    if inherits:
        upstream = layout()
    else:
        upstream = [GlobalArtifacts]
    
    token = Layout.set([*colls, *upstream])  # type: ignore
    try:
        yield
    finally:
        Layout.reset(token)


@overload
def instances(*, context: Literal[False] = False, nullaware: Literal[True] = True) -> MutableMapping[type, Any]:
    ...


@overload
def instances(*, context: Literal[False] = False, nullaware: Literal[False]) -> MutableMapping[type, Any] | None:
    ...


@overload
def instances(*, context: Literal[True], nullaware: bool = True) -> ContextManager[MutableMapping[type, Any]]:
    ...


def instances(
    *, context: bool = False, nullaware: bool = True
) -> MutableMapping[type, Any] | ContextManager[MutableMapping[type, Any]] | None:
    context_value = Instances.get(None)

    if not context:
        if nullaware:
            return context_value or {}
        return context_value

    @contextmanager
    def wrapper():
        nonlocal context_value

        if context_value is None:
            context_value = {}
            token = Instances.set(context_value)

            try:
                yield context_value
            finally:
                Instances.reset(token)
        else:
            yield context_value

    return wrapper()


@contextmanager
def provide(*instances_: Any):
    context_value = instances(nullaware=False)
    if context_value is None:
        raise RuntimeError("provide() can only be used when instances available")

    old_values = {type_: context_value[type_] for instance in instances_ if (type_ := type(instance)) in context_value}

    context_value.update({type(instance): instance for instance in instances_})
    yield
    context_value.update(old_values)


def instance_of(cls: type):
    return instances()[cls]


@standalone_context
def iter_artifacts(key: Any | None = None):
    collection = AccessStack.get(None)
    if collection is None:
        collection = {}
        AccessStack.set(collection)

    if key not in collection:
        stack = collection[key] = [-1]
    else:
        stack = collection[key]

    index = stack[-1]
    stack.append(index)

    start_offset = index + 1
    try:
        for stack[-1], content in enumerate(layout()[start_offset:], start=start_offset):
            yield content
    finally:
        stack.pop()
        if not stack:
            collection.pop(key, None)


class _WrapGenerator(Generic[R, Q, R1]):
    value: R1

    def __init__(self, gen: Generator[R, Q, R1]):
        self.gen = gen

    def __iter__(self) -> Generator[R, Q, R1]:
        self.value = yield from self.gen
        return self.value


def callee_of(target: Fn[Any, inTC] | FnImplement) -> inTC:
    from .fn import Fn
    from .fn.compose import EntitiesHarvest

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
