# Simple Inject

[中文文档](README_zh.md)

Simple Inject is a lightweight dependency injection library for Python. It provides an easy-to-use interface for managing dependencies across different namespaces and scopes.

## Features

- Dependency injection with namespaces
- Scoped dependencies using context managers
- Decorator for injecting dependencies into functions
- Support for default and custom namespaces

## Installation

You can install Simple Inject using pip:

```
pip install py-simple-inject
```

## Usage

### Basic Usage

```python
from simple_inject import provide, inject

# Provide a dependency
provide("config", {"api_key": "abc123"})

# Inject a dependency
config = inject("config")
print(config["api_key"])  # Output: abc123
```

### Using Namespaces

```python
from simple_inject import provide, inject

# Provide dependencies in different namespaces
provide("db", "production_db", namespace="production")
provide("db", "test_db", namespace="test")

# Inject dependencies from specific namespaces
prod_db = inject("db", namespace="production")
test_db = inject("db", namespace="test")

print(prod_db)  # Output: production_db
print(test_db)  # Output: test_db
```

### Using Scopes

```python
from simple_inject import provide, inject, dependency_scope

with dependency_scope("request"):
    provide("user", {"id": 1, "name": "Alice"})
    user = inject("user")
    print(user["name"])  # Output: Alice

# The "user" dependency is no longer available outside the scope
try:
    inject("user")
except KeyError:
    print("User not found")  # This will be printed
```

### Using the Inject Scope Decorator

```python
from simple_inject import provide, inject, inject_scope

@inject_scope("session")
def process_user():
    provide("session_id", "123456")
    session_id = inject("session_id")
    print(f"Processing user with session ID: {session_id}")

process_user()  # Output: Processing user with session ID: 123456

# The "session_id" dependency is no longer available after the function call
try:
    inject("session_id")
except KeyError:
    print("Session ID not found")  # This will be printed
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.