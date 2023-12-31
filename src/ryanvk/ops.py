from __future__ import annotations
from typing import TYPE_CHECKING, Any, MutableMapping, MutableSequence

from ._runtime import Layout, Instances, AccessStack, GlobalArtifacts
from contextlib import contextmanager
from .utilles import standalone_context
from .typing import inTC

if TYPE_CHECKING:
    from .fn.base import Fn
    from ryanvk.fn.record import FnRecord


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


def callee_of(fn: Fn[Any, inTC]) -> inTC:
    from ryanvk.fn.compose import EntitiesHarvest

    def wrapper(*args, **kwargs) -> Any:
        signature = fn.compose_instance.signature()
        for artifacts in iter_artifacts(signature):
            if signature in artifacts:
                record: FnRecord = artifacts[signature]
                define = record["define"]

                #token = upstream_staff.set(staff)
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
                    #upstream_staff.reset(token)
                    ...
        else:
            raise NotImplementedError

    return wrapper  # type: ignore

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
