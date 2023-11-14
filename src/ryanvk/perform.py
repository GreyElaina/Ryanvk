from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from ryanvk.staff import Staff

    from .collector import BaseCollector


class BasePerform:
    __collector__: ClassVar[BaseCollector]
    # spec said one perform declare / class only binds to one collector instance.
    # multi to single or reversed behavior or settings are both denied in spec,
    # and, be suggested, actually coding.

    __static__: ClassVar[bool] = True
    # when a perform is static, its lifespan won't execute,
    # which means dynamic endpoint cannot be used in the perform.

    staff: Staff

    def __init__(self, staff: Staff) -> None:
        self.staff = staff

    def __post_init__(self):
        ...

    @classmethod
    def apply_to(cls, map: dict[Any, Any]):
        map.update(cls.__collector__.artifacts)

    @asynccontextmanager
    async def lifespan(self):
        async with AsyncExitStack() as stack:
            # TODO: entity lifespan manage entry
            # 设计中，所有的 Perform 都需要在 Staff 中预先通过 maintain 获取实例；可以预先初始化一些给 Staff 用。
            yield self

    @classmethod
    def __post_collected__(cls, collect: BaseCollector):
        ...

    def __init_subclass__(cls, *, native: bool = False, static: bool = True) -> None:
        if native:
            return

        collector = cls.__collector__
        cls.__static__ = static

        for i in collector.collected_callbacks:
            i(cls)

        cls.__post_collected__(collector)
