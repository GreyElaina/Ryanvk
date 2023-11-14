from __future__ import annotations

from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from ._runtime import GLOBAL_GALLERY
from .perform import BasePerform

if TYPE_CHECKING:
    from .typing import P, R, SupportsCollect

T = TypeVar("T")


class BaseCollector:
    artifacts: dict[Any, Any]
    collected_callbacks: list[Callable[[type[BasePerform]], Any]]

    namespace: str | None = None
    identify: str | None = None

    def __init__(self, artifacts: dict[Any, Any] | None = None) -> None:
        self.artifacts = artifacts or {}
        self.collected_callbacks = [self.__post_collected__]

    def __post_collected__(self, cls: type[BasePerform]):
        self.cls = cls

        if self.namespace is not None:
            ns: dict = GLOBAL_GALLERY.setdefault(self.namespace, {})
            locate: dict = ns.setdefault(self.identify or "_", {})
            locate.update(self.artifacts)

    @property
    def _(self):
        class LocalPerformTemplate(BasePerform, native=True):
            __collector__ = self

        return LocalPerformTemplate

    def on_collected(self, func: Callable[[type], Any]):
        self.collected_callbacks.append(func)

    def remove_collected_callback(self, func: Callable[[type], Any]):
        self.collected_callbacks.remove(func)

    def using(self, context_manager: AbstractContextManager[T]) -> T:
        self.on_collected(lambda _: context_manager.__exit__(None, None, None))
        return context_manager.__enter__()

    def entity(
        self,
        signature: SupportsCollect[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        return signature.collect(self, *args, **kwargs)
