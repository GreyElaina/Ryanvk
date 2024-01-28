from __future__ import annotations

import sys
from collections import UserDict
from typing import Any, Iterable, Mapping, MutableMapping, MutableSequence, Protocol, TypeVar, runtime_checkable

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

_K = TypeVar("_K")
_V = TypeVar("_V")


class DetailedArtifacts(UserDict, MutableMapping[_K, _V]):
    protected: bool = False


@runtime_checkable
class ArtifactMirror(Protocol):
    def mirrors_target(self) -> Iterable[Mapping[Any, Any]]:
        ...


LayoutContentT: TypeAlias = "ArtifactMirror | DetailedArtifacts[Any, Any]"
LayoutT: TypeAlias = "MutableSequence[LayoutContentT]"
