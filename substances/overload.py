from __future__ import annotations

from typing import List, Protocol, Sequence, TypeVar, overload

from rye.builtins.overloads import SimpleOverload, TypeOverload
from rye.collector import BaseCollector
from rye.fn.base import Fn
from rye.fn.compose import FnCompose
from rye.operators import layout, using_sync
from rye.typing import FnComposeCallReturnType
from typing_extensions import reveal_type

m = BaseCollector()
T = TypeVar("T")


class TestPerform(m._):
    @m.collect
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

        @staticmethod
        def implement_sample(value: type[T]) -> T:
            ...


reveal_type(TestPerform.test)
reveal_type(TestPerform.test.__class__.implements)
reveal_type(TestPerform.test.implements)
reveal_type(TestPerform.test.implements(type=str))
reveal_type(TestPerform.test.implements(type=List[str]).__call__)


class TestPerformAlt((n := BaseCollector())._):
    @n.collect
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷闷作响，空气振振有声。"

    @n.collect
    @TestPerform.test.implements(type=int)
    def test_impl_(self, value: type[int]) -> int:
        return 25565

    #@n.collect
    @TestPerform.test.implements(type=Sequence[str])
    def test_impl_1(self, value: type[Sequence[str]]) -> Sequence[str]:
        ...




with using_sync(TestPerformAlt()):
    from devtools import debug

    debug(layout())

    debug(layout())

    b = TestPerform.test(str)
    reveal_type(TestPerform.test)
    c = TestPerform.test(int)

    print("??", repr(b), repr(c))
