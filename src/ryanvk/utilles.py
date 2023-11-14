from __future__ import annotations
import functools
from typing import Callable, Iterable, TypeVar
from contextvars import copy_context

from ryanvk.staff import P, R

T = TypeVar("T")


class NestableIterable(Iterable[T]):
    index_stack: list
    iterable: list[T]

    def __init__(self, iterable: list[T]) -> None:
        self.iterable = iterable
        self.index_stack = [-1]

    def __iter__(self):
        index = self.index_stack[-1]
        self.index_stack.append(index)

        start_offset = index + 1
        try:
            for self.index_stack[-1], content in enumerate(
                self.iterable[start_offset:],
                start=start_offset,
            ):
                yield content
        finally:
            self.index_stack.pop()


def standalone_context(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        cx = copy_context()
        # copy_context 是浅拷贝，只要约束 assign/initizate 就能完美运作。

        return cx.run(func, *args, **kwargs)

    return wrapper
