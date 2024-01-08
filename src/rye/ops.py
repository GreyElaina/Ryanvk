from __future__ import annotations

import inspect
import warnings
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Concatenate,
    ContextManager,
    Generator,
    Generic,
    Literal,
    MutableMapping,
    MutableSequence,
    TypeVar,
    overload,
)

from rye.fn.record import FnImplement
from rye.layout import DetailedArtifacts
from rye.topic import merge_topics_if_possible

from ._runtime import AccessStack, GlobalArtifacts, Instances, Layout, UpstreamArtifacts
from .typing import R1, P, Q, R, inTC
from .utils import standalone_context

if TYPE_CHECKING:
    from ._capability import CapabilityPerform
    from .fn import Fn
    from .fn.record import FnRecord
    from .perform import BasePerform


def layout() -> MutableSequence[DetailedArtifacts[Any, Any]]:
    return Layout.get(None) or [GlobalArtifacts]


def shallow():
    return layout()[0]


@contextmanager
def isolate(
    *collections: MutableMapping[Any, Any] | DetailedArtifacts,
    default_protected: bool = True,
    inherits: bool = True,
    protect_upstream: bool = True,
):
    colls = [*collections]

    for index, value in enumerate(colls):
        if not isinstance(value, DetailedArtifacts):
            v = DetailedArtifacts(value)
            v.protected = default_protected
            colls[index] = v
            
    if inherits:
        upstream = layout()
    else:
        upstream = [GlobalArtifacts]
    
    if protect_upstream:
        protected = [i for i in upstream if not i.protected]
    else:
        protected = []
    
    for protect_target in protected:
        protect_target.protected = True

    token = Layout.set([*colls, *upstream])  # type: ignore
    try:
        yield
    finally:
        for i in protected:
            i.protected = False
        Layout.reset(token)


@contextmanager
def mutable(target: DetailedArtifacts):
    target.protected = False
    try:
        yield
    finally:
        target.protected = True

@overload
def instances(*, context: Literal[False] = False, nullaware: Literal[True] = True) -> MutableMapping[type, Any]:
    ...


@overload
def instances(*, context: Literal[False] = False, nullaware: Literal[False]) -> MutableMapping[type, Any] | None:
    ...


@overload
def instances(*, context: Literal[True], nullaware: bool = True) -> ContextManager[MutableMapping[type, Any]]:
    ...


def instances(
    *, context: bool = False, nullaware: bool = True
) -> MutableMapping[type, Any] | ContextManager[MutableMapping[type, Any]] | None:
    context_value = Instances.get(None)

    if not context:
        if nullaware:
            return context_value or {}
        return context_value

    @contextmanager
    def wrapper():
        nonlocal context_value

        if context_value is None:
            context_value = {}
            token = Instances.set(context_value)

            try:
                yield context_value
            finally:
                Instances.reset(token)
        else:
            yield context_value

    return wrapper()


@contextmanager
def provide(*instances_: Any):
    context_value = instances(nullaware=False)
    if context_value is None:
        raise RuntimeError("provide() can only be used when instances available")

    old_values = {type_: context_value[type_] for instance in instances_ if (type_ := type(instance)) in context_value}

    context_value.update({type(instance): instance for instance in instances_})
    yield
    context_value.update(old_values)


def instance_of(cls: type):
    return instances()[cls]


@standalone_context
def iter_artifacts(key: Any | None = None):
    collection = AccessStack.get(None)
    if collection is None:
        collection = {}
        AccessStack.set(collection)

    if key not in collection:
        stack = collection[key] = [-1]
    else:
        stack = collection[key]

    index = stack[-1]
    stack.append(index)

    start_offset = index + 1
    try:
        for stack[-1], content in enumerate(layout()[start_offset:], start=start_offset):
            yield content
    finally:
        stack.pop()
        if not stack:
            collection.pop(key, None)


class _WrapGenerator(Generic[R, Q, R1]):
    value: R1

    def __init__(self, gen: Generator[R, Q, R1]):
        self.gen = gen

    def __iter__(self) -> Generator[R, Q, R1]:
        self.value = yield from self.gen
        return self.value


def callee_of(target: Fn[Any, inTC] | FnImplement) -> inTC:
    from .fn import Fn
    from .fn.compose import EntitiesHarvest

    def wrapper(*args, **kwargs) -> Any:
        if isinstance(target, Fn):
            signature = target.compose_instance.signature()
        else:
            signature = target

        for artifacts in iter_artifacts(signature):
            if signature in artifacts:
                record: FnRecord = artifacts[signature]
                define = record["define"]

                wrap = _WrapGenerator(define.compose_instance.call(*args, **kwargs))

                for harvest_info in wrap:
                    scope = record["overload_scopes"][harvest_info.name]
                    stage = harvest_info.overload.harvest(scope, harvest_info.value)
                    endpoint = EntitiesHarvest.mutation_endpoint.get(None)
                    if endpoint is not None:
                        endpoint.commit(stage)

                return wrap.value
        else:
            raise NotImplementedError

    return wrapper  # type: ignore


@overload
def is_implemented(perform: type[BasePerform] | BasePerform, target: type[CapabilityPerform]) -> bool:
    ...


@overload
def is_implemented(perform: type[BasePerform] | BasePerform, target: Fn) -> bool:
    ...


@overload
def is_implemented(
    perform: type[BasePerform] | BasePerform,
    target: Fn[Callable[Concatenate[Any, P], Any], Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> bool:
    ...


def is_implemented(
    perform: type[BasePerform] | BasePerform, target: type[CapabilityPerform] | Fn, *args, **kwargs
) -> bool:
    if not isinstance(perform, type):
        perform = perform.__class__

    if isinstance(target, type):
        for define in target.__collector__.definations:
            if define.compose_instance.signature() in perform.__collector__.artifacts:
                return True
    else:
        fn_sign = target.compose_instance.signature()
        pred = fn_sign in perform.__collector__.artifacts

        if not pred:
            return False

        if not (args or kwargs):
            return True

        record: FnRecord = perform.__collector__.artifacts[fn_sign]
        overload_scopes = record["overload_scopes"]

        slots = []

        for harvest_info in target.compose_instance.collect(Any, *args, **kwargs):
            sign = harvest_info.overload.digest(harvest_info.value)
            if harvest_info.name not in overload_scopes:
                return False
            scope = overload_scopes[harvest_info.name]
            twin_slot = harvest_info.overload.access(scope, sign)
            if twin_slot is None:
                return False
            slots.append(twin_slot)

        if slots and set(slots.pop()).intersection(*slots):
            return True

    return False

_T = TypeVar("_T")


def _gen_subclass(cls: type[_T]) -> Generator[type[_T], None, None]:
    yield cls
    for sub_cls in cls.__subclasses__():
        if TYPE_CHECKING:
            assert issubclass(sub_cls, cls)
        yield from _gen_subclass(sub_cls)


def namespace_generate(
    *,
    warning: bool = True,
    warn_for_accident_declare: bool = True,
    warn_for_non_static: bool = True,
):
    """
    NOTE
        *warning* 应在发布时**有把握的**被关闭，以降低在用户侧运行时整体应用的启动负担，在平时开发时则应尽可能的开启这个设置。

        *warn_for_accident_declare* 扫描可能被 import 引入，却没有被自动导入至 namespace 的 Perform，
        也即，被设计为在默认情况下，可能无意中使用了 `m.upstream_target = False` 设定的 Perform。

        *warn_for_non_static* 扫描声明了 static=False ，也即使用了 Perform 生命周期特性的项，
        在现有的约定中，属于协议实现的 Perform 不应该声明局部生命周期资源，这会带来非必要的负担，
        请使用 launart 提供的 Service、Broadcast Control 提供的生命周期钩子或是其他能提供等效形式的方法实现
        （通常可以达到同等或超出的效果），再使用 mountpoint handler 暴露给 Ryanvk World 访问。
            > 该特性暂时被禁用。
            > NOTE: Ryanvk 1.3 有意加入对 launart / bcc 等 host 的上下文自动托管 / 同步特性
    """
    from .collector import UpstreamCollector

    def wrapper(func: Callable[[], None | Generator[type[BasePerform], None, Any]]):
        namespace: dict[Any, Any] = {}
        manually = set()
        token = UpstreamArtifacts.set(namespace)

        before = None
        if warning:
            before = list(_gen_subclass(BasePerform))[1:]

        try:
            if inspect.isgeneratorfunction(func):
                for i in func():
                    manually.add(i)
                    merge_topics_if_possible([i.__collector__.artifacts], [namespace])  # type: ignore
            else:
                func()
        finally:
            UpstreamArtifacts.reset(token)

        if before is not None:
            for i in list(_gen_subclass(BasePerform))[1:]:
                if i.__native__:
                    continue

                if (
                    warn_for_accident_declare
                    and not i.__no_warn__
                    and not isinstance(i, UpstreamCollector)
                    and i not in manually
                ):
                    warnings.warn(
                        f'{i.__module__}:{i.__name__} does not use the "upstream_target = True" setting.'
                        "It may have been imported accidentally or not yielded by this generator."
                        "Both scenarios are likely unintended. Please have a developer review this.",
                        ImportWarning,
                    )

        return namespace

    return wrapper
