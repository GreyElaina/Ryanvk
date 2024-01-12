from __future__ import annotations

import inspect
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    TypeVar,
)

from rye._runtime import UpstreamArtifacts
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

        *warn_for_non_static* 扫描声明了 static=False ，也即使用了 Perform 生命周期特性的项，
        在现有的约定中，属于协议实现的 Perform 不应该声明局部生命周期资源，这会带来非必要的负担，
        请使用 launart 提供的 Service、Broadcast Control 提供的生命周期钩子或是其他能提供等效形式的方法实现
        （通常可以达到同等或超出的效果），再使用 mountpoint handler 暴露给 Ryanvk World 访问。
            > 该特性暂时被禁用。
            > NOTE: Ryanvk 1.3 有意加入对 launart / bcc 等 host 的上下文自动托管 / 同步特性
    """
    from rye.collector import UpstreamCollector

    def wrapper(func: Callable[[], None | Generator[type[BasePerform], None, Any]]):
        namespace: dict[Any, Any] = {}
        manually = set()
        token = UpstreamArtifacts.set(namespace)

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
            UpstreamArtifacts.reset(token)

        if before is not None:
            for i in list(_gen_subclass(BasePerform))[1:]:
                if i.__native__:
                    continue

                if (
                    warn_for_accident_declare
                    and not i.__no_warn__
                    and not isinstance(i, UpstreamCollector)
                    and i not in manually
                ):
                    warnings.warn(
                        f'{i.__module__}:{i.__name__} does not use the "upstream_target = True" setting.'
                        "It may have been imported accidentally or not yielded by this generator."
                        "Both scenarios are likely unintended. Please have a developer review this.",
                        ImportWarning,
                    )

        return namespace

    return wrapper
