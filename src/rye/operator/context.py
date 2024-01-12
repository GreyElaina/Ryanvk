from __future__ import annotations

from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    MutableSequence,
)

from rye._runtime import GlobalArtifacts, Layout, NewInstances
from rye.layout import DetailedArtifacts

if TYPE_CHECKING:
    pass


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
