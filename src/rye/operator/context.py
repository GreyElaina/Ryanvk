from __future__ import annotations

from contextlib import AsyncExitStack, ExitStack, asynccontextmanager, contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    MutableSequence,
)

from rye._runtime import GlobalArtifacts, Layout, NewInstances
from rye.layout import DetailedArtifacts
from rye.operator.isolate import isolate_instances, isolate_layout
from rye.topic import merge_topics_if_possible

if TYPE_CHECKING:
    from rye.perform import BasePerform


def layout() -> MutableSequence[DetailedArtifacts[Any, Any]]:
    return Layout.get(None) or [GlobalArtifacts]


def shallow():
    return layout()[0]


def instances():
    return NewInstances.get()


@contextmanager
def provide(*instances_: Any):
    context_value = instances()
    if context_value is None:
        raise RuntimeError("provide() can only be used when instances available")

    old_values = {type_: context_value[type_] for instance in instances_ if (type_ := type(instance)) in context_value}

    context_value.update({type(instance): instance for instance in instances_})
    yield
    context_value.update(old_values)


def instance_of(cls: type):
    return instances()[cls]


@contextmanager
def using_sync(*performs: BasePerform):
    from rye.lifespan import AsyncLifespan, Lifespan
    from rye.operator.context import instances

    with ExitStack() as stack:
        collection = [i.__collector__.artifacts for i in performs]

        for artifacts in collection:
            with isolate_layout():
                merge_topics_if_possible([artifacts], layout())

                if AsyncLifespan.compose_instance.signature() in artifacts:
                    raise RuntimeError("AsyncLifespan is not supported in sync_context()")

                if Lifespan.compose_instance.signature() in artifacts:
                    stack.enter_context(Lifespan.callee())

        stack.enter_context(isolate_layout())
        merge_topics_if_possible(collection, layout())

        stack.enter_context(isolate_instances())

        instance_record = instances()
        
        for instance in performs:
            instance_record[type(instance)] = instance
        
        yield


@asynccontextmanager
async def using_async(*performs: BasePerform):
    from rye.lifespan import AsyncLifespan, Lifespan

    async with AsyncExitStack() as stack:
        collections = [i.__collector__.artifacts for i in performs]

        for artifacts in collections:
            with isolate_layout():
                merge_topics_if_possible([artifacts], layout())

                if Lifespan.compose_instance.signature() in artifacts:
                    stack.enter_context(Lifespan.callee())

                if AsyncLifespan.compose_instance.signature() in artifacts:
                    await stack.enter_async_context(AsyncLifespan.callee())

        stack.enter_context(isolate_layout())
        merge_topics_if_possible(collections, layout())

        stack.enter_context(isolate_instances())

        instance_record = instances()
        
        for instance in performs:
            instance_record[type(instance)] = instance
        
        yield
