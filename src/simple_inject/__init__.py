from typing import Any, Literal, Optional

from .core import Inject, SimpleInject

__simple_inject = SimpleInject()


def provide(key: str, value: Any, namespace: str = 'default'):
    """
    Provide a dependency in the current context.

    Parameters
    ----------
    key : str
        The key to identify the dependency.
    value : Any
        The value of the dependency.
    namespace : str, optional
        The namespace for the dependency (default is 'default').
    """
    __simple_inject.provide(key, value, namespace)


def inject(
    key: str, namespace: str = 'default', if_not_found: Literal['none', 'raise'] = 'none'
) -> Any:
    """
    Inject a dependency.

    Parameters
    ----------
    key : str
        The key of the dependency to inject.
    namespace : str, optional
        The namespace of the dependency (default is 'default').

    Returns
    -------
    Any
        The value of the requested dependency.

    Raises
    ------
    DependencyNotFoundError
        If the requested dependency is not found in the given namespace.
    """
    return __simple_inject.inject(key, namespace, if_not_found)


def state(namespace: Optional[str] = None):
    return __simple_inject.state(namespace)


def create_scope():
    return __simple_inject.create_scope()


def scoped():
    return __simple_inject.scoped()


def purge(namespace: Optional[str] = None):
    """
    Purge the dependencies in the specified namespace.

    If no namespace is specified, all dependencies are purged.

    Parameters
    ----------
    namespace : str, optional
        The namespace to purge. If not specified, all dependencies are purged.
    """
    return __simple_inject.purge(namespace)


def auto_inject():
    return __simple_inject.auto_inject()
