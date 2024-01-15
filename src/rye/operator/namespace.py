from __future__ import annotations

import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    TypeVar,
)

from rye.topic import merge_topics_if_possible

if TYPE_CHECKING:
    from rye.perform import BasePerform


_T = TypeVar("_T")


def _gen_subclass(cls: type[_T]) -> Generator[type[_T], None, None]:
    yield cls
    for sub_cls in cls.__subclasses__():
        if TYPE_CHECKING:
            assert issubclass(sub_cls, cls)
        yield from _gen_subclass(sub_cls)


def namespace_generate(
    *,
    warning: bool = True,
    warn_for_accident_declare: bool = True,
    warn_for_non_static: bool = True,
):
    """
    NOTE
        *warning* 应在发布时**有把握的**被关闭，以降低在用户侧运行时整体应用的启动负担，在平时开发时则应尽可能的开启这个设置。

        *warn_for_accident_declare* 扫描可能被 import 引入，却没有被自动导入至 namespace 的 Perform，
        也即，被设计为在默认情况下，可能无意中使用了 `m.upstream_target = False` 设定的 Perform。

    """
    def wrapper(func: Callable[[], None | Generator[type[BasePerform], None, Any]]):
        namespace: dict[Any, Any] = {}
        manually = set()

        before = None
        if warning:
            before = list(_gen_subclass(BasePerform))[1:]

        try:
            if inspect.isgeneratorfunction(func):
                for i in func():
                    manually.add(i)
                    merge_topics_if_possible([i.__collector__.artifacts], [namespace])  # type: ignore
            else:
                func()
        finally:
            ...

        if before is not None:
            for i in list(_gen_subclass(BasePerform))[1:]:
                if i.__native__:
                    continue

        return namespace

    return wrapper
