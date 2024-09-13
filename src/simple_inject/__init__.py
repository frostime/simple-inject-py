from typing import Any, Dict

from .core import SimpleInject

__simple_inject = SimpleInject()


def provide(key: str, value: Any, namespace: str = 'default'):
    __simple_inject.provide(key, value, namespace)


def inject(key: str, namespace: str = 'default') -> Any:
    return __simple_inject.inject(key, namespace)


def dependency_scope(namespace: str = 'default'):
    return __simple_inject.dependency_scope(namespace)


def inject_scope(namespace: str = 'default'):
    return __simple_inject.inject_scope(namespace)
