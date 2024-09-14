# Simple Inject

[中文文档](README_zh.md)

Simple Inject is a lightweight dependency injection library for Python. It provides an easy-to-use interface for managing dependencies across different namespaces and scopes.

## Features

- Simple and intuitive API for dependency injection
- Support for multiple namespaces to isolate dependencies
- Scoped dependencies using context managers or decorators
- Nested scopes for fine-grained control
- Easy to integrate with existing projects
- Minimal overhead and dependencies

## Installation

You can install Simple Inject using pip:

```
pip install py-simple-inject
```

## Quick Start

Here's a simple example to get you started:

```python
from simple_inject import provide, inject, create_scope

# Provide a dependency
provide('config', {'debug': True})

# Inject a dependency
config = inject('config')
print(config['debug'])  # Output: True

# Use scopes to manage dependencies
with create_scope():
    provide('config', {'debug': False})
    config = inject('config')
    print(config['debug'])  # Output: False

# Outside the scope, the original value is preserved
config = inject('config')
print(config['debug'])  # Output: True
```

## API Reference

### `provide(key: str, value: Any, namespace: str = 'default')`

Provide a dependency in the current context.

### `inject(key: str, namespace: str = 'default') -> Any`

Inject a dependency from the current context.

### `create_scope()`

Create a new dependency scope. Use with a `with` statement.

### `scoped()`

A decorator to create a new dependency scope for a function.

### `purge(namespace: Optional[str] = None)`

Purge dependencies, either from a specific namespace or all namespaces.

## Advanced Usage

### Using Namespaces

```python
provide('key', 'value1', namespace='ns1')
provide('key', 'value2', namespace='ns2')

print(inject('key', namespace='ns1'))  # Output: value1
print(inject('key', namespace='ns2'))  # Output: value2
```

### Nested Scopes

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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.