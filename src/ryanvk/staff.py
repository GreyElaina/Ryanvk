from __future__ import annotations

from collections import ChainMap
from contextlib import AsyncExitStack, asynccontextmanager
from contextvars import ContextVar
from copy import copy
from typing import TYPE_CHECKING, Any, Callable, MutableMapping, Protocol, TypeVar, overload

from typing_extensions import ParamSpec

from ryanvk.utilles import standalone_context

if TYPE_CHECKING:
    from .perform import BasePerform

P = ParamSpec("P")
R = TypeVar("R", covariant=True)
VnCallable = TypeVar("VnCallable", bound=Callable)

_iter_stack_collection = ContextVar[dict[Any, list[int]]]("_CurrentIterStack")


class Staff:
    artifact_collections: list[MutableMapping[Any, Any]]
    components: dict[str, Any]
    exit_stack: AsyncExitStack
    instances: dict[type, Any]

    def __init__(
        self, artifacts_collections: list[MutableMapping[Any, Any]], components: dict[str, Any]
    ) -> None:
        self.artifact_collections = artifacts_collections
        self.components = components
        self.exit_stack = AsyncExitStack()
        self.instances = {}

    class PostInitShape(Protocol[P]):
        def __post_init__(self, *args: P.args, **kwargs: P.kwargs) -> Any:
            ...

    @overload
    def inject(
        self, perform_type: type[PostInitShape[P]], *args: P.args, **kwargs: P.kwargs
    ) -> None:
        ...

    @overload
    def inject(self, perform_type: type[BasePerform]) -> None:
        ...

    def inject(self, perform_type: ..., *args, **kwargs):
        perform = perform_type(self)
        perform.__post_init__(*args, **kwargs)
        self.artifact_collections.insert(0, perform.__collector__.artifacts)

    async def maintain(self, perform: BasePerform):
        await self.exit_stack.enter_async_context(perform.lifespan())

    @asynccontextmanager
    async def lifespan(self):
        async with self.exit_stack:
            yield self

    def ext(self, components: dict[str, Any]):
        instance = copy(self)
        instance.components.update(components)
        return instance

    @standalone_context
    def iter_artifacts(self, key: Any | None = None):
        collection = _iter_stack_collection.get(None)
        if collection is None:
            stack = [-1]
            _iter_stack_collection.set({key: stack})
        else:
            if key not in collection:
                collection[key] = [-1]

            stack = collection[key]

        index = stack[-1]
        stack.append(index)

        start_offset = index + 1
        try:
            for stack[-1], content in enumerate(
                self.artifact_collections[start_offset:], start=start_offset
            ):
                yield content
        finally:
            stack.pop()
