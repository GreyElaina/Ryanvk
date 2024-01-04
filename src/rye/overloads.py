from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rye.typing import Twin

from .fn.overload import FnOverload


@dataclass(eq=True, frozen=True)
class SimpleOverloadSignature:
    value: Any


class SimpleOverload(FnOverload[SimpleOverloadSignature, type[Any], Any]):
    def digest(self, collect_value: Any) -> SimpleOverloadSignature:
        return SimpleOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: SimpleOverloadSignature) -> dict[Twin, None]:
        if signature.value not in scope:
            target = scope[signature.value] = {}
        else:
            target = scope[signature.value]

        return target

    def harvest(self, scope: dict, value: Any) -> dict[Twin, None]:
        if value in scope:
            return scope[value]

        return {}


@dataclass(eq=True, frozen=True)
class TypeOverloadSignature:
    type: type[Any]


class TypeOverload(FnOverload[TypeOverloadSignature, type[Any], Any]):
    def digest(self, collect_value: type) -> TypeOverloadSignature:
        return TypeOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: TypeOverloadSignature) -> dict[Twin, None]:
        if signature.type not in scope:
            target = scope[signature.type] = {}
        else:
            target = scope[signature.type]

        return target

    def harvest(self, scope: dict, value: Any) -> dict[Twin, None]:
        t = type(value)
        if t in scope:
            return scope[t]

        return {}


class _SingletonOverloadSignature:
    ...


SINGLETON_SIGN = _SingletonOverloadSignature()


class SingletonOverload(FnOverload[None, None, None]):
    def digest(self, collect_value: None) -> _SingletonOverloadSignature:
        return SINGLETON_SIGN

    def collect(self, scope: dict, signature: _SingletonOverloadSignature) -> dict[Twin, None]:
        s = scope[None] = {}
        return s

    def harvest(self, scope: dict, value: None) -> dict[Twin, None]:
        return scope[None]
