from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Generic, Any, overload, cast
from typing_extensions import Self, Concatenate
from ryanvk.collector import BaseCollector

from ryanvk.entity import BaseEntity
from ryanvk.fn.base import K, Fn
from ryanvk.fn.compose import FnCompose
from ryanvk.fn.record import FnRecord
from ryanvk.typing import P, R, inRC, specifiedCollectP

from ryanvk.perform import BasePerform

if TYPE_CHECKING:
    from ryanvk.fn.overload import FnOverload


class FnImplementEntity(Generic[P, R, inRC, specifiedCollectP], BaseEntity):
    fn: Fn[P, R, Concatenate[Any, specifiedCollectP]]
    impl: Callable[..., Any]

    def __init__(
        self: FnImplementEntity[P, R, inRC, specifiedCollectP],
        fn: Fn[P, R, Concatenate[Any, specifiedCollectP]],
        impl: inRC,
        *args: specifiedCollectP.args,
        **kwargs: specifiedCollectP.kwargs,
    ):
        self.fn = fn
        self.impl = impl
        
        self._collect_args = args
        self._collect_kwargs = kwargs

    def collect(
        self: FnImplementEntity[P, R, inRC, specifiedCollectP],
        collector: BaseCollector,
    ):
        super().collect(collector)

        overload_enabled = type(self.fn.compose_instance).collect is FnCompose.collect
        record_signature = self.fn.compose_instance.signature()
        if record_signature not in collector.artifacts:
            record = collector.artifacts[record_signature] = cast(
                "FnRecord",
                {
                    "define": self,
                    "overload_enabled": overload_enabled,
                    "overload_scopes": {},
                    "legecy_slot": None,
                    "entities": {},
                },
            )
        else:
            record = collector.artifacts[record_signature]

        overload_scopes = record["overload_scopes"]
        twin = (collector, self.impl)

        if not overload_enabled:
            record["legecy_slot"] = twin  # type: ignore
            return self

        triples: set[tuple[str, FnOverload, Any]] = set()

        for harvest_info in self.fn.compose_instance.collect(*self._collect_args, **self._collect_kwargs):
            sign = harvest_info.overload.signature_from_collect(harvest_info.value)
            scope = overload_scopes.setdefault(harvest_info.name, {})
            harvest_info.overload.collect(scope, sign, twin)
            triples.add((harvest_info.name, harvest_info.overload, sign))

        record["entities"][frozenset(triples)] = twin

        return self

    @overload
    def __get__(
        self, instance: BasePerform, owner: type
    ) -> FnImplementEntityAgent[P, R, specifiedCollectP]:
        ...

    @overload
    def __get__(self, instance: Any, owner: type) -> Self:
        ...

    def __get__(self, instance: BasePerform | Any, owner: type):
        if not isinstance(instance, BasePerform):
            return self

        return FnImplementEntityAgent(instance, self)


class FnImplementEntityAgent(Generic[P, R, specifiedCollectP]):
    perfrom: BasePerform
    entity: FnImplementEntity[P, R, Any, specifiedCollectP]

    def __init__(
        self, perform: BasePerform, entity: FnImplementEntity[P, R, Any, specifiedCollectP]
    ) -> None:
        self.perform = perform
        self.entity = entity

    @property
    def staff(self):
        return self.perform.staff

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.entity.impl(self.perform, *args, **kwargs)

    def super(self, *args: P.args, **kwargs: P.kwargs) -> R:
        return self.entity.fn.call(self.staff, *args, **kwargs)
