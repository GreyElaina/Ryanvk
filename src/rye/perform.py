from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from .collector import BaseCollector


class BasePerform:
    __collector__: ClassVar[BaseCollector]
    # spec said one perform declare / class only binds to one collector instance.
    # multi to single or reversed behavior or settings are both denied in spec,
    # and, be suggested, actually coding.

    __native__: ClassVar[bool] = False
    # when a perform is native, its ALL collector-based functions will be disabled,
    # the __collector__ attribute is unavailable too.

    __static__: ClassVar[bool] = True
    # when a perform is static, its lifespan won't execute,
    # which means dynamic endpoint cannot be used in the perform.
    # and could be used in a widen context safely.

    __no_warn__: ClassVar[bool] = False
    # when a perform is labeled "no_warn",
    # `namespace_generate` won't complain anything related to the perform.

    def __post_init__(self):
        ...

    @classmethod
    def apply_to(cls, map: dict[Any, Any]):
        map.update(cls.__collector__.artifacts)

    @classmethod
    def __post_collected__(cls, collect: BaseCollector):
        ...

    def __init_subclass__(
        cls,
        *,
        keep_native: bool = False,
    ) -> None:
        cls.__native__ = keep_native
        if keep_native:
            return

        collector = cls.__collector__

        for i in collector.collected_callbacks:
            i(cls)

        cls.__post_collected__(collector)

