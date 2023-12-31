from __future__ import annotations

from typing import Any, Callable, Concatenate, Protocol, TypeVar, reveal_type, overload

from ryanvk.collector import BaseCollector
from ryanvk.fn.base import Fn
from ryanvk.fn.compose import FnCompose
from ryanvk.fn.overload import FnOverload
from ryanvk.overloads import TypeOverload, SimpleOverload
from ryanvk.typing import FnComposeCallReturnType, P, R
from ryanvk.ops import isolate, layout
from ryanvk.topic import merge_topics_if_possible

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.entity
    @Fn.compose
    class test(FnCompose):
        type = TypeOverload().as_agent()
        sim = SimpleOverload().as_agent()

        @overload
        def call(self, value: type[str]) -> FnComposeCallReturnType[str]:
            ...
        
        @overload
        def call(self, value: type[int]) -> FnComposeCallReturnType[int]:
            ...
        @overload
        def call(self, value: type[T]) -> FnComposeCallReturnType[T]:
            ...

        def call(self, value: type[T]) -> FnComposeCallReturnType[T]:
            with self.harvest() as entities:
                yield self.sim.call(value)

            #reveal_type(entities.first1()(value))
            reveal_type(entities.first1().test().test1()(value))
            return entities.first(value)

        class ShapeCall(Protocol[T]):
            def __call__(self, value: type[T]) -> T:
                ...

        @overload
        def collect(self, implement: ShapeCall[str], *, type: type[str]):
            ...
        
        @overload
        def collect(self, implement: ShapeCall[int], *, type: type[int]):
            ...

        @overload
        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            ...

        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            yield self.sim.collect(type)

reveal_type(TestPerform.test)
reveal_type(TestPerform.test.implements(type=str))
reveal_type(TestPerform.test.implements(type=list[str]).__call__)

class TestPerformAlt((n := BaseCollector())._):
    #@n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷闷作响，空气振振有声。"
    
    reveal_type(test_impl_int)

with isolate():
    from devtools import debug
    debug(layout())

    merge_topics_if_possible([
        TestPerformAlt.__collector__.artifacts  
    ], layout())


    debug(layout())

    b = TestPerform.test.callee(str)
    reveal_type(TestPerform.test)
    c = TestPerform.test.callee(int)

    print("??", repr(b))
