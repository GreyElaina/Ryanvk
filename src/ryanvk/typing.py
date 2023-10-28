from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, Protocol, Union, runtime_checkable

from typing_extensions import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R", infer_variance=True)


class SupportsCollect(Protocol[P, R]):
    def collect(self, collector: Any, *args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore
        ...


@runtime_checkable
class SupportsMerge(Protocol):
    def merge(self, *records: dict):
        ...
