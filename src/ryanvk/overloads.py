from __future__ import annotations
from ryanvk.collector import BaseCollector

from ryanvk.typing import Twin
from ryanvk._ordered_set import OrderedSet

from .fn.overload import FnOverload
from dataclasses import dataclass

from typing import Any, Callable, Sequence

@dataclass(eq=True, frozen=True)
class SimpleOverloadSignature:
    value: Any

class SimpleOverload(FnOverload[SimpleOverloadSignature, type[Any], Any]):
    def signature_from_collect(self, collect_value: Any) -> SimpleOverloadSignature:
        return SimpleOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: SimpleOverloadSignature, twin: Twin) -> None:
        if signature.value not in scope:
            target = scope[signature.value] = OrderedSet()
        else:
            target = scope[signature.value]
        
        target.add(twin)
    
    def harvest(self, scope: dict, value: Any) -> Sequence[tuple[BaseCollector, Callable[..., Any]]]:
        if value in scope:
            return scope[value]

        return ()

@dataclass(eq=True, frozen=True)
class TypeOverloadSignature:
    type: type[Any]

class TypeOverload(FnOverload[TypeOverloadSignature, type[Any], Any]):
    def signature_from_collect(self, collect_value: type) -> TypeOverloadSignature:
        return TypeOverloadSignature(collect_value)

    def collect(self, scope: dict, signature: TypeOverloadSignature, twin: Twin) -> None:
        if signature.type not in scope:
            target = scope[signature.type] = OrderedSet()
        else:
            target = scope[signature.type]
        
        target.add(twin)
    
    def harvest(self, scope: dict, value: Any) -> Sequence[tuple[BaseCollector, Callable[..., Any]]]:
        t =  type(value)
        if t in scope:
            return scope[t]

        return ()


class _SingletonOverloadSignature:
    ...

SINGLETON_SIGN = _SingletonOverloadSignature()

class SingletonOverload(FnOverload[None, None, None]):
    def signature_from_collect(self, collect_value: None) -> _SingletonOverloadSignature:
        return SINGLETON_SIGN

    def collect(self, scope: dict, signature: _SingletonOverloadSignature, twin: Twin) -> None:
        scope[None] = twin
    
    def harvest(self, scope: dict, value: None) -> Sequence[tuple[BaseCollector, Callable[..., Any]]]:
        return OrderedSet([scope[None]])
