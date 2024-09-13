# Simple Inject

Simple Inject 是一个轻量级的 Python 依赖注入库。它提供了一个易于使用的接口，用于管理跨不同命名空间和作用域的依赖项。

## 特性

- 支持命名空间的依赖注入
- 使用上下文管理器实现作用域依赖
- 用于向函数注入依赖的装饰器
- 支持默认和自定义命名空间

## 安装

你可以使用 pip 安装 Simple Inject：

```
pip install py-simple-inject
```

## 使用方法

### 基本用法

```python
from simple_inject import provide, inject

# 提供一个依赖
provide("config", {"api_key": "abc123"})

# 注入一个依赖
config = inject("config")
print(config["api_key"])  # 输出: abc123
```

### 使用命名空间

```python
from simple_inject import provide, inject

# 在不同的命名空间中提供依赖
provide("db", "production_db", namespace="production")
provide("db", "test_db", namespace="test")

# 从特定的命名空间中注入依赖
prod_db = inject("db", namespace="production")
test_db = inject("db", namespace="test")

print(prod_db)  # 输出: production_db
print(test_db)  # 输出: test_db
```

### 使用作用域

```python
from simple_inject import provide, inject, dependency_scope

with dependency_scope("request"):
    provide("user", {"id": 1, "name": "Alice"})
    user = inject("user")
    print(user["name"])  # 输出: Alice

# 在作用域外，"user" 依赖不再可用
try:
    inject("user")
except KeyError:
    print("未找到用户")  # 这行将被打印
```

### 使用注入作用域装饰器

```python
from simple_inject import provide, inject, inject_scope

@inject_scope("session")
def process_user():
    provide("session_id", "123456")
    session_id = inject("session_id")
    print(f"正在处理会话 ID 为 {session_id} 的用户")

process_user()  # 输出: 正在处理会话 ID 为 123456 的用户

# 函数调用后，"session_id" 依赖不再可用
try:
    inject("session_id")
except KeyError:
    print("未找到会话 ID")  # 这行将被打印
```

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

该项目使用 MIT 许可证。