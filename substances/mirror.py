from __future__ import annotations

from typing import Protocol, TypeVar

from rye._runtime import AccessStack, GlobalArtifacts, IteratingKey
from rye.builtins.overloads import SimpleOverload, TypeOverload
from rye.collector import BaseCollector
from rye.fn.base import Fn
from rye.fn.compose import FnCompose
from rye.layout import DetailedArtifacts, LayoutT
from rye.operators import instances, isolate_layout, iter_artifacts, layout, using_sync
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

        def call(self, value: type[T]) -> FnComposeCallReturnType[T]:
            with self.harvest() as entities:
                yield self.sim.call(value)

            return entities.first(value)

        class ShapeCall(Protocol[T]):
            def __call__(self, value: type[T]) -> T:
                ...

        def collect(self, implement: ShapeCall[T], *, type: type[T]):
            yield self.sim.collect(type)


class TestPerformAlt((n := BaseCollector())._):
    @n.collect
    @TestPerform.test.implements(type=str)
    def test_impl_int(self, value: type[str]) -> str:
        return "手杖闷闷作响，空气振振有声。"

    reveal_type(TestPerform.test.implements)


class TestMirror:
    def mirror_iter_key(self):
        return "balabala"

    def mirrors_target(self) -> LayoutT:
        return [DetailedArtifacts({1: 1}), DetailedArtifacts({2: 2}), DetailedArtifacts({3: 3})]


with isolate_layout(), using_sync(TestPerformAlt()):
    from devtools import debug

    debug(layout())

    # merge_topics_if_possible([TestPerformAlt.__collector__.artifacts], layout())

    debug(layout(), instances())

    b = TestPerform.test(str)

    print("??", repr(b))


with isolate_layout():
    layout().insert(0, TestMirror())
    debug(layout())

    for i in iter_artifacts():
        if 2 in i:
            for ii in iter_artifacts():
                print("p", ii)
            