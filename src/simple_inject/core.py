from collections import defaultdict
from contextvars import ContextVar
from functools import wraps
from typing import Any, Dict, Optional


class DependencyNotFoundError(Exception):
    """Exception raised when a requested dependency is not found."""
    pass

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

    def inject(self, key: str, namespace: str = 'default') -> Any:
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
        context = self._context.get()
        if key in context[namespace]:
            return context[namespace][key]
        raise DependencyNotFoundError(
            f"Dependency '{key}' not found in namespace '{namespace}'"
        )

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