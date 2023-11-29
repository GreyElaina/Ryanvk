from __future__ import annotations

from typing import Any, Protocol, TYPE_CHECKING, TypeVar, overload

if TYPE_CHECKING:
    from ryanvk.perform import BasePerform

T = TypeVar("T")
P = TypeVar("P", bound="BasePerform")


class LifespanManager(Protocol):
    async def maintain(self, perform: BasePerform) -> None:
        ...
    
    async def close_all(self) -> None:
        ...
    
    def get_instance(self, cls: type[P]) -> P:
        ...


class MountpointProvider(Protocol):
    @overload
    def get(self, identity: str) -> Any:
        ...
    
    @overload
    def get(self, identity: type[T]) -> T:
        ...
    
    @overload
    def set(self, identity: str, value: Any) -> None:
        ...
    
    @overload
    def set(self, identity: type[T], value: T) -> None:
        ...
