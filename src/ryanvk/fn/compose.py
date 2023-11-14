from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING
from contextvars import ContextVar

from ryanvk.fn.record import FnImplement

from ryanvk.typing import (
    CallShape,
    P,
    R,
    FnComposeCallReturnType,
    FnComposeCollectReturnType,
    Twin,
)

if TYPE_CHECKING:
    from ryanvk.staff import Staff  # noqa: F401
    from ryanvk.fn.base import Fn

_StaffCtx = ContextVar["Staff"]("_StaffCtx")


class FnCompose(ABC):
    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    @property
    def collector(self):
        return self.fn.collector

    @property
    def staff(self):
        return _StaffCtx.get()

    @abstractmethod
    def call(self) -> FnComposeCallReturnType[Any]:
        ...

    def entity_type(self: CallShape[P, R]):  # type: ignore
        return self.call

    def collect(self, **kwargs: Any) -> FnComposeCollectReturnType:
        ...

    def signature(self):
        return FnImplement(self.fn)

    def harvest_entity(self, *choices: set[Twin]):
        choicess = list(choices)
        final_choice = choicess.pop().intersection(choicess)
        collector, raw_entity = list(final_choice).pop()

        instance = self.staff.instances[collector.cls]

        def wrapper(*args, **kwargs):
            return raw_entity(instance, *args, **kwargs)

        return wrapper
