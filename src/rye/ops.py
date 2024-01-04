from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Generator, Generic, MutableMapping

from rye.fn.record import FnImplement

from ._runtime import AccessStack, GlobalArtifacts, Instances, Layout
from .typing import R1, Q, R, inTC
from .utilles import standalone_context

if TYPE_CHECKING:
    from .fn import Fn
    from .fn.record import FnRecord


def layout():
    return Layout.get(None) or [GlobalArtifacts]


def shallow():
    return layout()[0]


@contextmanager
def isolate(*collections: MutableMapping[Any, Any]):
    token = Layout.set([*collections, GlobalArtifacts])
    try:
        yield
    finally:
        Layout.reset(token)


def instances(*, context: bool = False) -> MutableMapping[type, Any]:
    context_value = Instances.get(None)

    if not context:
        return context_value or {}

    if context_value is None:
        context_value = {}
        Instances.set(context_value)

    return context_value


@contextmanager
def provide(*instances_: Any):
    context_value = instances(context=True)
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
