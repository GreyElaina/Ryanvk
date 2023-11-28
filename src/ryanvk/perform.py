from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING, Any, ClassVar, Generator, Callable, TypeVar
import inspect
import warnings

from ryanvk.topic import merge_topics_if_possible
from ._runtime import targets_artifact_map

if TYPE_CHECKING:
    from ryanvk.staff import Staff

    from .collector import BaseCollector


class BasePerform:
    __collector__: ClassVar[BaseCollector]
    # spec said one perform declare / class only binds to one collector instance.
    # multi to single or reversed behavior or settings are both denied in spec,
    # and, be suggested, actually coding.

    __native__: ClassVar[bool] = False

    __static__: ClassVar[bool] = True
    # when a perform is static, its lifespan won't execute,
    # which means dynamic endpoint cannot be used in the perform.
    # and could be used in a widen context safely.

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

    def __init_subclass__(
        cls,
        *,
        keep_native: bool = False,
        static: bool = True,
    ) -> None:
        cls.__native__ = keep_native
        if keep_native:
            return

        collector = cls.__collector__
        cls.__static__ = static

        for i in collector.collected_callbacks:
            i(cls)

        cls.__post_collected__(collector)


_T = TypeVar("_T")


def _gen_subclass(cls: type[_T]) -> Generator[type[_T], None, None]:
    yield cls
    for sub_cls in cls.__subclasses__():
        if TYPE_CHECKING:
            assert issubclass(sub_cls, cls)
        yield from _gen_subclass(sub_cls)


def namespace_generate(*, warn_for_accident_declare: bool = True):
    """
    NOTE
        *warn_for_accident_declare* 应在发布时**有把握的**被关闭，以降低在用户侧运行时整体应用的启动负担，
        在平时开发时应该尽可能的开启这个设置，扫描可能被 import 引入，却没有被自动导入 namespace 的 Perform，
        也即，被设计为在默认情况下，可能无意中使用了 `m.upstream_target = False` 的 Perform。
    """

    def wrapper(func: Callable[[], None | Generator[type[BasePerform], None, Any]]):
        namespace: dict[Any, Any] = {}
        manually = set()
        token = targets_artifact_map.set(namespace)

        before = None
        if warn_for_accident_declare:
            before = list(_gen_subclass(BasePerform))[1:]

        try:
            if inspect.isgeneratorfunction(func):
                for i in func():
                    manually.add(i)
                    merge_topics_if_possible([i.__collector__.artifacts], [namespace])
        finally:
            targets_artifact_map.reset(token)

        if before is not None:
            for i in list(_gen_subclass(BasePerform))[1:]:
                if i.__native__:
                    continue

                if not i.__collector__.upstream_target and i not in manually:
                    warnings.warn(
                        f'{i.__name__} does not use the "upstream_target = True" setting.'
                        "It may have been imported accidentally or not yielded by this generator."
                        "Both scenarios are likely unintended. Please have a developer review this.",
                        ImportWarning,
                    )

        return namespace

    return wrapper
