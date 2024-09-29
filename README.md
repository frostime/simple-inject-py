# Simple Inject

[中文 README](README_zh.md)

Simple Inject is a lightweight Python dependency injection library. It provides an easy-to-use interface for managing dependencies across different namespaces and scopes.

## Features

- Simple and intuitive dependency injection API
- Supports multiple namespaces to isolate dependencies
- Implements scoped dependencies using context managers or decorators
- Supports nested scopes for fine-grained control
- Supports automatic dependency injection through parameters
- Easy integration with existing projects
- Minimal overhead and dependencies

## Installation

You can install Simple Inject using pip:

```
pip install py-simple-inject
```

## Quick Start

### Basic Usage

Here is a simple example demonstrating basic dependency injection and scope management:

```python
from simple_inject import provide, inject, create_scope

# Provide a dependency
provide('config', {'debug': True})

# Inject a dependency
config = inject('config')
print(config['debug'])  # Output: True
```

### Using Namespaces

```py
from simple_inject import provide, inject, create_scope

provide('key', 'value1', namespace='ns1')
provide('key', 'value2', namespace='ns2')

print(inject('key', namespace='ns1'))  # Output: value1
print(inject('key', namespace='ns2'))  # Output: value2
```

### Using Scopes

```py
provide('config', {'debug': True})

# Use scopes to manage dependencies
with create_scope():
    provide('config', {'debug': False})
    config = inject('config')
    print(config['debug'])  # Output: False

# Outside the scope, the original value is preserved
config = inject('config')
print(config['debug'])  # Output: True
```

Scopes can also be used with the `scoped` decorator:

```py
@scoped()
def scoped_function():
    provide('key', 'scoped_value')
    return inject('key')

provide('key', 'outer_value')
print(inject('key'))  # Output: outer_value
print(scoped_function())  # Output: scoped_value
print(inject('key'))  # Output: outer_value
```

### Nested Scopes

Scoped scopes can be nested, and dependencies in inner scopes will override those in outer scopes.

```python
provide('key', 'outer')

with create_scope():
    provide('key', 'inner')
    print(inject('key'))  # Output: inner

    with create_scope():
        provide('key', 'innermost')
        print(inject('key'))  # Output: innermost

    print(inject('key'))  # Output: inner

print(inject('key'))  # Output: outer
```

### Automatic Injection via Function Parameters

Simple Inject also supports automatic injection via function parameters. The following example demonstrates how to use this advanced feature:

```python
from simple_inject import provide, inject, create_scope, auto_inject, Inject

class Engine:
    def start(self):
        print("Engine started")

# Provide a dependency
provide('engine', Engine())

# Manually inject a dependency
engine = inject('engine')
engine.start()  # Output: Engine started

# Use automatic injection
@auto_inject()
def drive(car: str, engine: Engine = Inject('engine')):
    print(f"Driving {car}")
    engine.start()

drive("Tesla")  # Output: Driving Tesla and Engine started

# Use scopes to manage dependencies
with create_scope():
    provide('engine', Engine())  # Provide a new Engine instance
    drive("BMW")  # Output: Driving BMW and Engine started

# Outside the scope, the original value is preserved
drive("Toyota")  # Output: Driving Toyota and Engine started
```

## API Reference

### `provide(key: str, value: Any, namespace: str = 'default')`

Provides a dependency in the current context.

### `inject(key: str, namespace: str = 'default') -> Any`

Injects a dependency from the current context.

### `create_scope()`

Creates a new dependency scope. Used with the `with` statement.

### `scoped()`

Decorator to create a new dependency scope for a function.

### `auto_inject()`

Decorator to automatically inject parameters marked with `Inject`.

### `Inject(key: str, namespace: str = 'default')`

Class to mark a parameter for automatic injection.

### `purge(namespace: Optional[str] = None)`

Clears dependencies, either for a specific namespace or for all namespaces.

## Contributing

Contributions are welcome! Feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.