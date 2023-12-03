from __future__ import annotations

from typing import Any, Callable, Concatenate, Protocol, TypeVar, reveal_type

from ryanvk.collector import BaseCollector
from ryanvk.fn.base import Fn
from ryanvk.fn.compose import FnCompose
from ryanvk.fn.overload import FnOverload
from ryanvk.overloads import TypeOverload, SimpleOverload
from ryanvk.staff import Staff
from ryanvk.typing import FnComposeCallReturnType, P, R

from ryanvk.topic import merge_topics_if_possible

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.entity
    @Fn.compose
    class test(FnCompose):
        type = TypeOverload().as_agent()
        sim = SimpleOverload().as_agent()

        def call(self, value: type[T]) -> FnComposeCallReturnType[T]:
            with self.harvest() as entities:
                yield self.sim.call(value)

            return entities.first(value)

        class ShapeCall(Protocol[T]):
            def __call__(self, value: type[T]) -> T:
                ...

        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            yield self.sim.collect(type)

    @m.entity
    @Fn.compose
    @Fn.symmetric
    def test1(self, value: type[T]) -> T:
        ...

reveal_type(TestPerform.test)
reveal_type(TestPerform.test1)

class TestPerformAlt((n := BaseCollector())._):
    @n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷闷作响，空气振振有声。"

    @n.entity
    @TestPerform.test1.implements()
    def test1_impl(self, value: type[str]) -> str:
        print("symmetric test")
        return "星荧随挥舞而生，散落空中，颤颤作动。"
    
    reveal_type(test_impl_int)
    reveal_type(test1_impl)

class TestPerformAlt1((n := BaseCollector())._):
    @n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        print(self.test_impl_int.super(value))
        return "多层测试 - Alt1"

class TestPerformAlt2((n := BaseCollector())._):
    @n.entity
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        print(self.test_impl_int.super(value))
        return "多层测试 - Alt2"

    @n.entity
    @TestPerform.test1.implements()
    def test1_impl(self, value: type[str]) -> str:
        print("symmetric tes2t", self.test1_impl.super(value))
        return "素月分辉，明河共影，表里俱澄澈。"

a = Staff([TestPerformAlt.__collector__.artifacts], {})

merge_topics_if_possible([
    TestPerformAlt2.__collector__.artifacts,
    TestPerformAlt1.__collector__.artifacts
], a.artifact_collections)

#a.artifact_collections = [
#    TestPerformAlt2.__collector__.artifacts,
#    TestPerformAlt1.__collector__.artifacts,
#    TestPerformAlt.__collector__.artifacts
#]
from devtools import debug

#debug(a.artifact_collections)
b = TestPerform.test.call1(a)(str)
c = TestPerform.test1.call1(a)(str)
#d = TestPerform.test.call2(str)(str)

print("??", repr(b), repr(c))
