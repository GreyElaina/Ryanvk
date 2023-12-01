from __future__ import annotations
from typing import Any, Callable, Concatenate, Protocol, TypeVar

from ryanvk.collector import BaseCollector
from ryanvk.fn.base import Fn
from ryanvk.fn.compose import FnCompose
from ryanvk.fn.overload import FnOverload
from ryanvk.overloads import TypeOverload, SimpleOverload
from ryanvk.staff import Staff
from ryanvk.typing import FnComposeCallReturnType, P, R

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.entity
    @Fn.compose
    class test(FnCompose):
        type = TypeOverload().as_agent()
        sim = SimpleOverload().as_agent()

        def call(self, value: type[T]):
            with self.harvest() as entities:
                yield self.sim.call(value)

            print(entities._incompleted_result)
            return entities.first(value)

        class ShapeCall(Protocol[T]):
            def __call__(self, value: type[T]) -> T:
                ...

        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            yield self.sim.collect(type)


n = BaseCollector()

class TestPerformAlt(n._):
    @n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷声作响，空气振振有声。"


a = Staff([TestPerformAlt.__collector__.artifacts], {})

print(TestPerformAlt.__collector__.artifacts)
b = TestPerform.test.call1(a)(str)
print("??", repr(b))
