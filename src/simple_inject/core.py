import inspect
from collections import defaultdict
from contextvars import ContextVar
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Literal,
    Optional,
    TypeVar,
    get_type_hints,
)

T = TypeVar('T')


class DependencyNotFoundError(Exception):
    """Exception raised when a requested dependency is not found."""

    pass


class Inject(Generic[T]):
    """Marker class for injection."""

    def __init__(self, key: str, namespace: str = 'default'):
        self.key = key
        self.namespace = namespace


class SimpleInject:
    def __init__(self):
        self._context: ContextVar[Dict[str, Dict[str, Any]]] = ContextVar(
            'context', default=defaultdict(dict)
        )

    def provide(self, key: str, value: Any, namespace: str = 'default'):
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
        context = self._context.get()
        context[namespace][key] = value
        self._context.set(context)

    def inject(
        self,
        key: str,
        namespace: str = 'default',
        if_not_found: Literal['none', 'raise'] = 'none',
    ) -> Any:
        """
        Inject a dependency.

        Parameters
        ----------
        key : str
            The key of the dependency to inject.
        namespace : str, optional
            The namespace of the dependency (default is 'default').
        if_not_found : {'none', 'raise'}, optional
            What to do if the dependency is not found (default is 'none').
            - 'none' : return None.
            - 'raise' : raise a DependencyNotFoundError.

        Returns
        -------
        Any
            The value of the requested dependency.

        Raises
        ------
        DependencyNotFoundError
            If the requested dependency is not found in the given namespace.
        """
        context = self._context.get()
        if key in context[namespace]:
            return context[namespace][key]
        elif if_not_found == 'none':
            return None
        else:
            raise DependencyNotFoundError(
                f"Dependency '{key}' not found in namespace '{namespace}'"
            )

    def state(self, namespace: Optional[str] = None):
        """Get the state of the dependency injection context.


        Parameters
        ----------
        - `namespace` : `Optional[str]`, optional
            - The namespace to get the state of. If not specified, the state of all namespaces is returned.

        Returns
        ----------
        - `Dict[str, Dict[str, Any]]`
            - The state of the dependency injection context.
        """
        all_context = self._context.get()
        if namespace is None:
            return dict(all_context)
        else:
            return all_context[namespace]

    def create_scope(self):
        """
        Create a new dependency scope.

        Returns
        -------
        ScopeManager
            A context manager for the new dependency scope.
        """

        class ScopeManager:
            def __init__(self, outer_self):
                self.outer_self = outer_self
                self.token = None
                self.previous_context = None

            def __enter__(self):
                self.previous_context = self.outer_self._context.get()
                new_context = defaultdict(dict)
                for namespace, deps in self.previous_context.items():
                    new_context[namespace] = deps.copy()
                self.token = self.outer_self._context.set(new_context)

            def __exit__(self, exc_type, exc_value, traceback):
                self.outer_self._context.reset(self.token)

        return ScopeManager(self)

    def scoped(self):
        """
        Decorator to create a new dependency scope for a function.

        Returns
        -------
        Callable
            A decorator function that creates a new dependency scope.
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.create_scope():
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def purge(self, namespace: Optional[str] = None):
        """
        Purge the dependencies in the specified namespace.

        If no namespace is specified, all dependencies are purged.

        Parameters
        ----------
        namespace : str, optional
            The namespace to purge. If not specified, all dependencies are purged.
        """
        context = self._context.get()
        if namespace is not None:
            context[namespace].clear()
        else:
            context.clear()
        self._context.set(context)

    def auto_inject(self):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                sig = inspect.signature(func)
                type_hints = get_type_hints(func)

                for param_name, param in sig.parameters.items():
                    if param_name in kwargs:
                        continue

                    annotation = type_hints.get(param_name, inspect.Parameter.empty)
                    if isinstance(annotation, type) and issubclass(annotation, Inject):
                        inject_instance = annotation()
                        kwargs[param_name] = self.inject(
                            inject_instance.key, inject_instance.namespace
                        )
                    elif isinstance(param.default, Inject):
                        kwargs[param_name] = self.inject(
                            param.default.key, param.default.namespace
                        )

                return func(*args, **kwargs)

            return wrapper

        return decorator
