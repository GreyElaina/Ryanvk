from __future__ import annotations

from typing import Any, AsyncContextManager, Awaitable, Callable, ContextManager, Protocol, Self

from rye.fn import Fn


class LifespanHostShape(Protocol):
    def maintain_sync_task(self, task: Callable[[Self], Any]) -> None:
        ...

    def resolve_sync_tasks(self) -> None:
        ...


class AsyncLifespanHostShape(Protocol):
    def maintain_async_task(self, impl: Callable[[Self], Awaitable[None]]) -> None:
        ...

    async def resolve_async_tasks(self) -> None:
        ...


@Fn.symmetric
def Lifespan() -> ContextManager[None]:
    ...


@Fn.symmetric
def AsyncLifespan() -> AsyncContextManager[None]:
    ...
