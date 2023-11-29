from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING, Any, Callable, Iterable, MutableMapping, TypedDict

from ryanvk.topic import PileTopic
from ryanvk.typing import Twin

if TYPE_CHECKING:
    from ryanvk.collector import BaseCollector
    from ryanvk.fn.overload import FnOverload
    from .base import Fn


class FnRecord(TypedDict):
    define: Fn
    overload_enabled: bool
    overload_scopes: dict[str, dict[Any, Any]]
    legecy_slot: tuple[BaseCollector, Callable] | None
    entities: dict[frozenset[tuple[str, 'FnOverload', Any]] | None, Twin]


@dataclass(eq=True, frozen=True)
class FnImplement(PileTopic[FnRecord, tuple[tuple[str, 'FnOverload', Any], ...], Twin]):
    fn: Fn

    def iter_entities(
        self, record: FnRecord
    ) -> MutableMapping[frozenset[tuple[str, 'FnOverload', Any]] | None, Twin]:
        if record['overload_enabled']:
            return record["entities"]
        else:
            assert record['legecy_slot'] is not None

            return {None: record['legecy_slot']}

    def insist_objects(self, record: FnRecord) -> Iterable[Any]:
        return [*record["entities"].keys(), *record["entities"].values()]

    def has_entity(
        self,
        record: FnRecord,
        signature: tuple[tuple[str, 'FnOverload', Any], ...],
    ) -> bool:
        return signature in record["entities"]

    def get_entity(
        self,
        record: FnRecord,
        signature: frozenset[tuple[str, 'FnOverload', Any]] | None,
    ) -> Twin:
        return record["entities"][signature]

    def flatten_on(
        self,
        record: FnRecord,
        signature: tuple[tuple[str, 'FnOverload', Any], ...],
        entity: Twin,
    ) -> None:
        if not record['overload_enabled']:
            record['legecy_slot'] = entity
            return

        scopes = record['overload_scopes']
        for segment in signature:
            name, fn_overload, sign = segment
            if name not in scopes:
                scope = scopes[name] = {}
            else:
                scope = scopes[name]

            fn_overload.collect(scope, sign, entity)


# TODO: 弃用 Harvest，因为让我很烦。
# 只要只是在 ExtControl 和 Call/Collect Body 之间传递就好，先 make it work.
@dataclass(eq=True, frozen=True)
class FnOverloadHarvest:
    name: str
    overload: FnOverload
    value: Any
