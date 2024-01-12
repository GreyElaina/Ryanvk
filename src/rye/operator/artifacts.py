from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
)

from rye._runtime import AccessStack
from rye.operator.context import layout
from rye.utils import standalone_context

if TYPE_CHECKING:
    pass


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
