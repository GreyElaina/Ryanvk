from __future__ import annotations

from typing import Protocol, TypeVar, reveal_type

from rye._runtime import GlobalArtifacts
from rye.collector import BaseCollector
from rye.fn.base import Fn
from rye.fn.compose import FnCompose
from rye.ops import is_implemented, isolate, layout
from rye.overloads import SimpleOverload, TypeOverload
from rye.topic import merge_topics_if_possible
from rye.typing import FnComposeCallReturnType

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.collect
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

    @m.collect
    @Fn.symmetric
    @staticmethod
    def test1(value: type[T]) -> T:
        ...


reveal_type(TestPerform.test)
reveal_type(TestPerform.test.implements)
reveal_type(TestPerform.test.implements(type=str))
reveal_type(TestPerform.test1)


class TestPerformAlt((n := BaseCollector())._):
    @n.collect
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷闷作响，空气振振有声。"

    @n.collect
    @TestPerform.test1.implements()  # type: ignore
    def test1_impl(self, value: type[str]) -> str:
        print("symmetric test")
        return "星荧随挥舞而生，散落空中，颤颤作动。"


class TestPerformAlt1((n := BaseCollector())._):
    @n.collect
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        print(self.test_impl_int.super(value))
        return "多层测试 - Alt1"


class TestPerformAlt2((n := BaseCollector())._):
    @n.collect
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        print(self.test_impl_int.super(value))
        return "多层测试 - Alt2"

    # @n.entity
    # @TestPerform.test1.implements()
    def test1_impl(self, value: type[str]) -> str:
        print("symmetric tes2t", self.test1_impl.super(value))
        return "素月分辉，明河共影，表里俱澄澈。"

    reveal_type(TestPerform.test)
    reveal_type(TestPerform.test1)
    reveal_type(TestPerform.test.implements)
    reveal_type(TestPerform.test1.implements())


# a = Staff([TestPerformAlt.__collector__.artifacts], {})


with isolate():
    from devtools import debug

    debug(layout())

    merge_topics_if_possible(
        [
            TestPerformAlt2.__collector__.artifacts,
            TestPerformAlt1.__collector__.artifacts,
            TestPerformAlt.__collector__.artifacts,
        ],
        layout(),
    )

    debug(layout())
    debug(GlobalArtifacts)

    b = TestPerform.test.callee(str)
    print("111", is_implemented(TestPerformAlt, TestPerform.test))
    print("222", is_implemented(TestPerformAlt, TestPerform.test, type=str))
    print("222", is_implemented(TestPerformAlt, TestPerform.test, type=int))
    c = TestPerform.test1.callee(str)

    print("??", repr(b), repr(c))
