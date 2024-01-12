from __future__ import annotations

from collections import ChainMap
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
)

from rye._runtime import Layout, NewInstances
from rye.operator.context import instances, layout

if TYPE_CHECKING:
    pass


@contextmanager
def isolate_layout(backwards_protect: bool = True):
    upstream = layout()

    if backwards_protect:
        protected = [i for i in upstream if not i.protected]
    else:
        protected = []

    for protect_target in protected:
        protect_target.protected = True

    token = Layout.set([*upstream])
    try:
        yield
    finally:
        for i in protected:
            i.protected = False
        Layout.reset(token)


@contextmanager
def isolate_instances():
    current_layout = instances()
    token = NewInstances.set(ChainMap({}, *current_layout.maps))

    try:
        yield
    finally:
        NewInstances.reset(token)
