from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from contextvars import ContextVar
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Generator,
    Generic,
    Iterable,
    Self,
    Sequence,
)
from ryanvk._runtime import _upstream_staff
from ryanvk._ordered_set import OrderedSet
from ryanvk.fn.record import FnImplement
from ryanvk.typing import (
    CallShape,
    FnComposeCallReturnType,
    FnComposeCollectReturnType,
    P,
    R,
    Twin,
)
from ryanvk.overloads import SingletonOverload

if TYPE_CHECKING:
    from ryanvk.fn.base import Fn
    from ryanvk.staff import Staff  # noqa: F401


class FnCompose(ABC):
    singleton = SingletonOverload().as_agent()

    fn: Fn

    def __init__(self, fn: Fn):
        self.fn = fn

    @property
    def collector(self):
        return self.fn.collector

    @property
    def staff(self):
        return _upstream_staff.get()

    @abstractmethod
    def call(self) -> FnComposeCallReturnType[Any]:
        ...

    def collect(self, implement: Callable, **kwargs: Any) -> FnComposeCollectReturnType:
        ...

    def signature(self):
        return FnImplement(self.fn)

    @contextmanager
    def harvest(self: CallShape[P, R]) -> Generator[EntitiesHarvest[P, R], None, None]:
        harv = EntitiesHarvest(self.staff)  # type: ignore
        tok = EntitiesHarvest.mutation_endpoint.set(harv)

        # i prefer not to rewrite a Protocol for just a "self.staff"

        try:
            yield harv
        finally:
            harv.finished = True
            EntitiesHarvest.mutation_endpoint.reset(tok)


class EntitiesHarvest(Generic[P, R]):
    mutation_endpoint: ClassVar[ContextVar[Self]] =\
        ContextVar("EntitiesHarvest.mutation_endpoint")  # fmt: off

    finished: bool = False
    _incompleted_result: OrderedSet[Twin] | None = None

    staff: Staff

    def __init__(self, staff: Staff):
        self.staff = staff

    def commit(self, inbound: Sequence[Twin]) -> None:
        if self._incompleted_result is None:
            self._incompleted_result = OrderedSet(inbound)
            return

        self._incompleted_result.intersection_update(inbound)

    @property
    def ensured_result(self):
        if not self.finished or self._incompleted_result is None:
            raise LookupError(
                "attempts to read result before its mutations all finished"
            )

        return self._incompleted_result

    """
    def resolve_perform_param(self, twin: Twin) -> Callable[P, R]:
        # TODO, 诶不这个是拿来干什么的来着。
        ...
    """

    def ensure_twin(self, twin: Twin) -> Callable[P, R]:
        # 然后是 instance maintainer，同时也是 lifespan manager，不过因为我的原因会把他们分开来。
        # TODO: 这个还是之后再说，先拿 Staff 和 Static Perform 顶上。
        collector, implement = twin

        if collector.cls not in self.staff.instances:
            instance = self.staff.instances[collector.cls] = collector.cls(self.staff)
        else:
            instance = self.staff.instances[collector.cls]

        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return implement(instance, *args, **kwargs)

        return wrapper

    @property
    def first(self) -> Callable[P, R]:
        return self.ensure_twin(next(iter(self.ensured_result)))

    def iter_result(self) -> Iterable[Callable[P, R]]:
        return map(self.ensure_twin, self.ensured_result)
