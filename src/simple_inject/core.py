from contextvars import ContextVar
from typing import Any, Dict


class SimpleInject:
    def __init__(self):
        self._global_dependencies: Dict[str, Dict[str, Any]] = {}
        self._context_dependencies: ContextVar[Dict[str, Dict[str, Any]]] = ContextVar(
            'context_dependencies', default={'default': {}}
        )

    def provide(self, key: str, value: Any, namespace: str = 'default'):
        context_deps = self._context_dependencies.get()
        if namespace not in context_deps:
            context_deps[namespace] = {}
        context_deps[namespace][key] = value
        self._context_dependencies.set(context_deps)

    def inject(self, key: str, namespace: str = 'default') -> Any:
        context_deps = self._context_dependencies.get()
        if namespace in context_deps and key in context_deps[namespace]:
            return context_deps[namespace][key]

        if (
            namespace in self._global_dependencies
            and key in self._global_dependencies[namespace]
        ):
            return self._global_dependencies[namespace][key]

        raise KeyError(f"Dependency '{key}' not found in namespace '{namespace}'")

    def dependency_scope(self, namespace: str = 'default'):
        class ScopeManager:
            def __init__(self, outer_self):
                self.outer_self = outer_self
                self.token = None
                self.previous_context = None

            def __enter__(self):
                self.previous_context = self.outer_self._context_dependencies.get()
                new_context = {k: v.copy() for k, v in self.previous_context.items()}
                if namespace not in new_context:
                    new_context[namespace] = {}
                else:
                    new_context[namespace] = new_context[namespace].copy()
                self.token = self.outer_self._context_dependencies.set(new_context)

            def __exit__(self, exc_type, exc_value, traceback):
                self.outer_self._context_dependencies.reset(self.token)

        return ScopeManager(self)

    def inject_scope(self, namespace: str = 'default'):
        def decorator(func):
            from functools import wraps

            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.dependency_scope(namespace):
                    return func(*args, **kwargs)

            return wrapper

        return decorator
