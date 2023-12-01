from __future__ import annotations
from typing import Any, Callable, Concatenate, Protocol, TypeVar

from ryanvk.collector import BaseCollector
from ryanvk.fn.base import Fn
from ryanvk.fn.compose import FnCompose
from ryanvk.fn.overload import FnOverload
from ryanvk.overloads import TypeOverload
from ryanvk.staff import Staff
from ryanvk.typing import FnComposeCallReturnType, P, R

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.entity
    @Fn.compose
    class test(FnCompose):
        type = TypeOverload().as_agent()

        def call(self, value: type[T]) -> FnComposeCallReturnType[T]:
            with self.harvest() as entities:
                yield self.type.call(value)

            return entities.first(value)  # type: ignore

        class ShapeCall(Protocol[T]):
            def __call__(self, value: type[T]) -> T:
                ...

        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            yield self.type.collect(type)


n = BaseCollector()

class TestPerformAlt(n._):
    @n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return ""


a = Staff([TestPerformAlt.__collector__.artifacts], {})

b = TestPerform.test.call(a, str)
