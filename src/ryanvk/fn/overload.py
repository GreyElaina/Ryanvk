from __future__ import annotations
from typing import Any, Callable, Generic, Sequence, TypeVar, TYPE_CHECKING, overload
from typing_extensions import Self
from ryanvk.collector import BaseCollector
from ryanvk.fn.record import FnOverloadHarvest
from ryanvk.typing import Twin

if TYPE_CHECKING:
    from .compose import FnCompose

On = TypeVar("On", bound="FnOverload", covariant=True)
TCallValue = TypeVar("TCallValue")
TCollectValue = TypeVar("TCollectValue")
TSignature = TypeVar("TSignature")


class FnOverload(Generic[TSignature, TCollectValue, TCallValue]):
    def __init__(self) -> None:
        ...

    def signature_from_collect(self, collect_value: TCollectValue) -> TSignature:
        return collect_value  # type: ignore

    def collect(self, scope: dict, signature: TSignature, twin: Twin) -> None:
        scope[signature] = twin

    def harvest(
        self, scope: dict, value: TCallValue
    ) -> Sequence[tuple[BaseCollector, Callable]]:
        return scope[value]

    def as_agent(self):
        return FnOverloadAgentDescriptor(self)


class FnOverloadAgent(Generic[On]):
    name: str
    compose: FnCompose
    fn_overload: On

    def __init__(self, name: str, fn: FnCompose, overload: On):
        self.name = name
        self.compose = fn
        self.fn_overload = overload

    def collect(
        self: FnOverloadAgent[FnOverload[Any, TCollectValue, Any]], value: TCollectValue
    ):
        return FnOverloadHarvest(self.name, self.fn_overload, value)

    def call(
        self: FnOverloadAgent[FnOverload[Any, Any, TCallValue]], value: TCallValue
    ):
        return FnOverloadHarvest(self.name, self.fn_overload, value)


class FnOverloadAgentDescriptor(Generic[On]):
    name: str
    fn_overload: On

    def __init__(self, fn_overload: On) -> None:
        self.fn_overload = fn_overload

    def __set_name__(self, name: str, owner: type):
        self.name = name

    @overload
    def __get__(self, instance: None, owner: type) -> Self:
        ...

    @overload
    def __get__(self, instance: FnCompose, owner: type) -> FnOverloadAgent[On]:
        ...

    def __get__(self, instance: FnCompose | None, owner: type):
        if instance is None:
            return self

        return FnOverloadAgent(self.name, instance, self.fn_overload)
