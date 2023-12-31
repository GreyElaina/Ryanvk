from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from typing import (
    TYPE_CHECKING,
    AbstractSet,
    Any,
    Callable,
    ClassVar,
    Concatenate,
    Generator,
    Generic,
    Iterable,
    Self,
)

from ryanvk._ordered_set import OrderedSet
from ryanvk.fn.record import FnImplement
from ryanvk.ops import instances
from ryanvk.overloads import SingletonOverload
from ryanvk.typing import (
    Detour1,
    FnComposeCallReturnType,
    FnComposeCollectReturnType,
    ImplementForCollect,
    P,
    T,
    R,
    Twin,
    WrapCall,
    inRC,
    unspecifiedCollectP,
    specifiedCollectP,
    inTC, DbgSlot
)

if TYPE_CHECKING:
    from ryanvk.fn.base import Fn


class FnCompose(ABC):
    singleton = SingletonOverload().as_agent()

    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    @property
    def collector(self):
        return self.fn.collector

    @abstractmethod
    def call(self) -> FnComposeCallReturnType[Any]:
        ...

    def collect(self, implement: Callable, **kwargs: Any) -> FnComposeCollectReturnType:
        ...

    def signature(self):
        return FnImplement(self.fn)

    # TODO: 使用 pyright#6822 中的一些未成系统的技巧输出 Overload Callable.
    @property
    def harvest(
        self: ImplementForCollect[inTC]
    ):
        @contextmanager
        def wrapper() -> Generator[EntitiesHarvest[inTC], None, None]:
            harv = EntitiesHarvest()
            tok = EntitiesHarvest.mutation_endpoint.set(harv)

            try:
                yield harv
            finally:
                harv.finished = True
                EntitiesHarvest.mutation_endpoint.reset(tok)
        
        return wrapper




class EntitiesHarvest(Generic[inRC]):
    mutation_endpoint: ClassVar[ContextVar[Self]] =\
        ContextVar("EntitiesHarvest.mutation_endpoint")  # fmt: off

    finished: bool = False
    _incompleted_result: OrderedSet[Twin] | None = None

    def commit(self, inbound: AbstractSet[Twin]) -> None:
        if self._incompleted_result is None:
            self._incompleted_result = OrderedSet(inbound)
            return

        self._incompleted_result.intersection_update(inbound)

    @property
    def ensured_result(self):
        if not self.finished or self._incompleted_result is None:
            raise LookupError("attempts to read result before its mutations all finished")

        return self._incompleted_result

    def ensure_twin(self, twin: Twin) -> Callable:
        # 然后是 instance maintainer，同时也是 lifespan manager，不过因为我的原因会把他们分开来。
        # TODO: 这个还是之后再说，先拿 Staff 和 Static Perform 顶上。
        collector, implement = twin
        instances_context = instances(context=True)

        if collector.cls not in instances_context:
            instance = instances_context[collector.cls] = collector.cls()
        else:
            instance = instances_context[collector.cls]

        def wrapper(*args, **kwargs):
            return implement(instance, *args, **kwargs)

        return wrapper  # type: ignore

    # 这里必须依赖于 `overload-transforming` 这个行为。
    # 我突然感觉我提的那个 issue 最后又会被 as designed 了。

    def first1(self: EntitiesHarvest[Callable[Concatenate[T, specifiedCollectP], Any]]) -> DbgSlot[Callable[[], T]]:
        ...

    @property
    def first(self: EntitiesHarvest[Callable[Concatenate[WrapCall[P, R], specifiedCollectP], Any]]) -> Callable[specifiedCollectP, Callable[[WrapCall[P ,R]], Any]]:
        return self.ensure_twin(self.ensured_result[0])

    def iter_result(self: EntitiesHarvest[Concatenate[inTC, ...]]) -> Iterable[inTC]:
        return map(self.ensure_twin, self.ensured_result)
