from __future__ import annotations

from typing import AsyncContextManager, ContextManager

from rye.fn import Fn


@Fn.symmetric
def Lifespan() -> ContextManager[None]:
    ...


@Fn.symmetric
def AsyncLifespan() -> AsyncContextManager[None]:
    ...
