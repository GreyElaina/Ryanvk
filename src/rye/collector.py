from __future__ import annotations

from contextlib import AbstractContextManager
from typing import TYPE_CHECKING, Any, Callable, MutableMapping, TypeVar

from typing_extensions import Self

from ._runtime import ArtifactDest
from .perform import BasePerform

if TYPE_CHECKING:
    from .typing import P, R, SupportsCollect

T = TypeVar("T")


class BaseCollector:
    artifacts: MutableMapping[Any, Any]
    collected_callbacks: list[Callable[[type[BasePerform]], Any]]

    def __init__(self, artifacts: dict[Any, Any] | None = None) -> None:
        self.artifacts = artifacts or {}
        self.collected_callbacks = [self.__post_collected__]

    def __post_collected__(self, cls: type[BasePerform]):
        self.cls = cls

    @property
    def _(self):
        class LocalPerformTemplate(BasePerform, keep_native=True):
            __collector__ = self

        return LocalPerformTemplate

    def on_collected(self, func: Callable[[type], Any]):
        self.collected_callbacks.append(func)

    def remove_collected_callback(self, func: Callable[[type], Any]):
        self.collected_callbacks.remove(func)

    def using(self, context_manager: AbstractContextManager[T]) -> T:
        self.on_collected(lambda _: context_manager.__exit__(None, None, None))
        return context_manager.__enter__()

    def collect(
        self,
        signature: SupportsCollect[Self, P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        return signature.collect(self, *args, **kwargs)


class UpstreamCollector(BaseCollector):
    def __init__(self, artifacts: dict[Any, Any] | None = None) -> None:
        super().__init__(artifacts)
        
        value = ArtifactDest.get(None)
        if value is None:
            raise RuntimeError("UpstreamCollector must be used with a available upstream.")
    
        