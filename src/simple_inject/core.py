import inspect
import warnings
from collections import defaultdict
from contextvars import ContextVar
from copy import deepcopy
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

_SENTINEL = object()


class DependencyNotFoundError(Exception):
    """Exception raised when a requested dependency is not found."""

    pass


class Inject(Generic[T]):
    """Marker class for injection."""

    def __init__(self, key: str, namespace: str = 'default'):
        self.key = key
        self.namespace = namespace


class ScopeManager:
    def __init__(self, outer_self: 'SimpleInject', deep_copy: bool):
        self.outer_self = outer_self
        self.token = None
        self.previous_context = None
        self.deep_copy = deep_copy
        self._provided_keys = {}  # Track keys provided in this scope
        self._original_provide = None  # Store original provide method

    def __enter__(self):
        self.previous_context = self.outer_self._get_context()

        # Create new context for the scope
        new_context = defaultdict(dict)
        for namespace, deps in self.previous_context.items():
            if self.deep_copy:
                new_context[namespace] = deepcopy(deps)
            else:
                new_context[namespace] = deps.copy()
        self.token = self.outer_self._context.set(new_context)

        # Add this scope to the stack for tracking
        self._scope_active = True
        self.outer_self._scope_stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Mark scope as inactive to stop tracking provides
        self._scope_active = False

        # Remove this scope from the stack
        if self.outer_self._scope_stack and self.outer_self._scope_stack[-1] is self:
            self.outer_self._scope_stack.pop()

        # Save the final state for 'All' policy before resetting
        current_context = self.outer_self._get_context()
        self._scope_final_state = {}
        for namespace, deps in current_context.items():
            if self.deep_copy:
                self._scope_final_state[namespace] = deepcopy(deps)
            else:
                self._scope_final_state[namespace] = deps.copy()

        # Reset the context
        self.outer_self._context.reset(self.token)

    def scoped_state(
        self,
        policy: Literal['Provided', 'All'] = 'Provided',
        namespace: Optional[str] = None,
    ):
        """
        Get the state within the scope.

        Parameters
        ----------
        policy : {'Provided', 'All'}, optional
            - 'Provided': Only return dependencies that were provided within the scope
            - 'All': Return the complete state within the scope
        namespace : Optional[str], optional
            Specific namespace to get state from. If None, returns state from all namespaces.

        Returns
        -------
        Dict[str, Any] or Dict[str, Dict[str, Any]]
            The state according to the specified policy and namespace.

        Raises
        ------
        RuntimeError
            If called before the scope has exited.
        """
        # Check if scope is still active
        if getattr(self, '_scope_active', True):
            raise RuntimeError('scoped_state can only be called after exiting the scope')

        if policy == 'All':
            result = getattr(self, '_scope_final_state', {})
        else:  # policy == 'Provided'
            result = dict(self._provided_keys)

        # Filter by namespace if specified
        if namespace is not None:
            return result.get(namespace, {})

        # Return a copy to prevent external modification
        if isinstance(result, dict):
            return {k: dict(v) if isinstance(v, dict) else v for k, v in result.items()}
        return result


class SimpleInject:
    def __init__(self):
        self._context: ContextVar[Dict[str, Dict[str, Any]]] = ContextVar('context')
        self._scope_stack: list['ScopeManager'] = []  # Stack to track active scopes

    def _get_context(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the current context, initializing it if it doesn't exist.
        """
        context = self._context.get(_SENTINEL)
        if context is _SENTINEL:
            context = defaultdict(dict)
            self._context.set(context)
        return context

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
        # Track this provide operation in the most recent active scope
        if self._scope_stack:
            current_scope = self._scope_stack[-1]
            if current_scope._scope_active:
                if namespace not in current_scope._provided_keys:
                    current_scope._provided_keys[namespace] = {}

                # Store the value according to deep_copy setting
                if current_scope.deep_copy:
                    current_scope._provided_keys[namespace][key] = deepcopy(value)
                else:
                    # For shallow copy, we need to store a copy to avoid
                    # later modifications affecting our record
                    current_scope._provided_keys[namespace][key] = (
                        self._safe_shallow_copy(value)
                    )

        context = self._get_context()
        context[namespace][key] = value
        self._context.set(context)

    def update(
        self,
        key: str,
        updater: Callable[[T], T],
        namespace: str = 'default',
        if_not_found: Literal['none', 'raise'] = 'none',
    ):
        """
        Update a dependency in the current context.

        Parameters
        ----------
        key : str
            The key of the dependency to update.
        updater : (oldValue: T) -> T
            The updater function.
        namespace : str, optional
            The namespace of the dependency to update (default is 'default').
        if_not_found : {'none', 'raise'}, optional
            What to do if the dependency is not found (default is 'none').
            - 'none' : do nothing.
            - 'raise' : raise a DependencyNotFoundError.

        Raises
        ------
        DependencyNotFoundError
            If the requested dependency is not found in the given namespace.
        """
        old = self.inject(key, namespace, if_not_found=if_not_found)
        new = updater(old)
        self.provide(key, new, namespace)

    def has(self, key: str, namespace: str = 'default') -> bool:
        """
        Check if a dependency exists in the current context.

        Parameters
        ----------
        key : str
            The key of the dependency to check.
        namespace : str, optional
            The namespace of the dependency (default is 'default').

        Returns
        -------
        bool
            True if the dependency exists, False otherwise.
        """
        context = self._get_context()
        return key in context[namespace]

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
        context = self._get_context()
        if key in context[namespace]:
            return context[namespace][key]
        elif if_not_found == 'none':
            warnings.warn(
                f"Dependency '{key}' not found in namespace '{namespace}'",
                UserWarning,
                source=self.inject,
            )
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
        all_context = self._get_context()
        if namespace is None:
            return dict(all_context)
        else:
            return all_context[namespace]

    def create_scope(self, deep: bool = False):
        """
        Create a new dependency scope.

        Parameters
        ----------
        deep : bool, optional
            If True, performs a deep copy of the dependencies, providing
            complete isolation between scopes. If False (default), performs a
            shallow copy, which is faster but may lead to shared state for
            mutable dependencies.

        Returns
        -------
        ScopeManager
            A context manager for the new dependency scope.
        """

        return ScopeManager(self, deep)

    def scoped(self, deep: bool = False):
        """
        Decorator to create a new dependency scope for a function.

        Parameters
        ----------
        deep : bool, optional
            If True, the scope will be created with a deep copy of dependencies.
            See `create_scope` for more details.

        Returns
        -------
        Callable
            A decorator function that creates a new dependency scope.
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.create_scope(deep=deep):
                    return func(*args, **kwargs)

            return wrapper

        return decorator

    def _safe_shallow_copy(self, value: Any) -> Any:
        """
        Safely create a shallow copy of a value.

        For objects with a copy() method, use it. For immutable types,
        return the value directly. For other mutable types, attempt
        various copy strategies.
        """
        # Immutable types can be returned directly
        if isinstance(value, (str, int, float, bool, tuple, frozenset, type(None))):
            return value

        # Try the copy() method first
        if hasattr(value, 'copy') and callable(getattr(value, 'copy')):
            try:
                return value.copy()
            except (AttributeError, TypeError):
                pass

        # For lists, use list() constructor
        if isinstance(value, list):
            return list(value)

        # For sets, use set() constructor
        if isinstance(value, set):
            return set(value)

        # For dicts, use dict() constructor
        if isinstance(value, dict):
            return dict(value)

        # For other types, return the reference (best effort)
        return value

    def purge(self, namespace: Optional[str] = None):
        """
        Purge the dependencies in the specified namespace.

        If no namespace is specified, all dependencies are purged.

        Parameters
        ----------
        namespace : str, optional
            The namespace to purge. If not specified, all dependencies are purged.
        """
        context = self._get_context()
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
