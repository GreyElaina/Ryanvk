from __future__ import annotations
from itertools import chain, cycle
from typing import (
    Any,
    Callable,
    Iterable,
    MutableMapping,
    TypeVar,
    Generic,
)

T = TypeVar("T")
S = TypeVar("S")
E = TypeVar("E")
K = TypeVar("K")


def _groupby(
    entities: Iterable[T], key: Callable[[T], K]
) -> MutableMapping[K, list[T]]:
    result = {}
    for i in entities:
        k = key(i)
        if k not in result:
            a = result[k] = []
        else:
            a = result[k]
        a.append(i)
    return result


class Topic(Generic[T]):
    def merge(self, inbound: list[T], outbound: list[T]) -> None:
        ...

    def new_record(self) -> T:
        ...


class PileTopic(Generic[T, S, E], Topic[T]):
    def iter_entities(self, record: T) -> MutableMapping[S, E]:
        ...

    def insist_objects(self, record: T) -> Iterable[Any]:
        ...

    def has_entity(self, record: T, signature: S) -> bool:
        ...

    def get_entity(self, record: T, signature: S) -> E:
        ...

    def flatten_on(
        self, record: T, signature: S, entity: E, replacement: E | None
    ) -> None:
        ...

    def merge(self, inbound: list[T], outbound: list[T]) -> None:
        outbound_depth = len(outbound)

        entities = chain(
            *[
                list(self.iter_entities(inbound_item).items())
                for inbound_item in inbound
            ]
        )
        for signature, group in _groupby(entities, key=lambda x: x[0]).items():
            # group: list[(Signature, Entity / Twin)]
            outbound_index = 0
            for group_inx in cycle(range(len(group))):
                # FIXME: use cycle(enumerate(range))

                if group[group_inx] is None:
                    break

                _, entity = group[group_inx]
                if outbound_index == outbound_depth:
                    outbound_depth += 1
                    outbound.append({self: self.new_record()})

                if self.has_entity(outbound[outbound_index][self], signature):
                    e = self.get_entity(outbound[outbound_index][self], signature)
                    group[group_inx] = (signature, e)
                    self.flatten_on(
                        outbound[outbound_index][self], signature, entity, e
                    )
                else:
                    group[group_inx] = None  # type: ignore
                    self.flatten_on(
                        outbound[outbound_index][self], signature, entity, None
                    )

                outbound_index += 1
                # print(outbound_index, outbound_depth, key, group, i)


def merge_topics_if_possible(
    inbounds: list[MutableMapping[Any, Any]],
    outbound: list[MutableMapping[Any, Any]],
    *,
    replace_non_topic: bool = True,
) -> None:
    topic_pair_records: dict[Topic, list[Any]] = {}

    done_replace = set()

    for pairs in inbounds:
        for maybe_topic, record in pairs.items():
            if isinstance(maybe_topic, Topic):
                if maybe_topic not in topic_pair_records:
                    pair_v = topic_pair_records[maybe_topic] = []
                else:
                    pair_v = topic_pair_records[maybe_topic]

                pair_v.append(record)
            elif replace_non_topic and maybe_topic not in done_replace:
                outbound[0][maybe_topic] = record
                done_replace.add(maybe_topic)

    for topic, records in topic_pair_records.items():
        if topic not in outbound[0]:
            outbound[0][topic] = topic.new_record()

        topic.merge(records, outbound)
