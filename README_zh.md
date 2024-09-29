# Simple Inject

[English](README.md)

Simple Inject 是一个轻量级的 Python 依赖注入库。它提供了一个易于使用的接口，用于管理跨不同命名空间和作用域的依赖关系。

## 特性

- 简单直观的依赖注入 API
- 支持多个命名空间以隔离依赖
- 使用上下文管理器或装饰器实现作用域依赖
- 支持嵌套作用域以实现精细控制
- 支持通过参数自动注入依赖
- 易于与现有项目集成
- 最小化开销和依赖

## 安装

你可以使用 pip 安装 Simple Inject：

```
pip install py-simple-inject
```

## 快速开始

### 基础用法

以下是一个简单的示例，展示了基本的依赖注入和作用域管理：

```python
from simple_inject import provide, inject, create_scope

# 提供一个依赖
provide('config', {'debug': True})

# 注入一个依赖
config = inject('config')
print(config['debug'])  # 输出：True
```

### 使用命名空间 (namespace)

```py
from simple_inject import provide, inject, create_scope

provide('key', 'value1', namespace='ns1')
provide('key', 'value2', namespace='ns2')

print(inject('key', namespace='ns1'))  # 输出：value1
print(inject('key', namespace='ns2'))  # 输出：value2

```

### 使用作用域 (scope)

```py
provide('config', {'debug': True})

# 使用作用域管理依赖
with create_scope():
    provide('config', {'debug': False})
    config = inject('config')
    print(config['debug'])  # 输出：False

# 在作用域之外，原始值得以保留
config = inject('config')
print(config['debug'])  # 输出：True
```

scope 作用域还可以通过装饰器 `scoped` 来使用:

```py
@scoped()
def scoped_function():
    provide('key', 'scoped_value')
    return inject('key')


provide('key', 'outer_value')
print(inject('key'))  # 输出：outer_value
print(scoped_function())  # 输出：scoped_value
print(inject('key'))  # 输出：outer_value
```

### 嵌套作用域

Scoped 作用域可以嵌套，内部作用域的依赖会覆盖外部作用域的依赖。

```python
provide('key', 'outer')

with create_scope():
    provide('key', 'inner')
    print(inject('key'))  # 输出：inner

    with create_scope():
        provide('key', 'innermost')
        print(inject('key'))  # 输出：innermost

    print(inject('key'))  # 输出：inner

print(inject('key'))  # 输出：outer
```

### 通过函数参数自动注入

Simple Inject 还支持通过函数参数进行自动注入。以下示例展示了如何使用这个高级功能：

```python
from simple_inject import provide, inject, create_scope, auto_inject, Inject

class Engine:
    def start(self):
        print("引擎启动")

# 提供一个依赖
provide('engine', Engine())

# 手动注入一个依赖
engine = inject('engine')
engine.start()  # 输出：引擎启动

# 使用自动注入
@auto_inject()
def drive(car: str, engine: Engine = Inject('engine')):
    print(f"驾驶 {car}")
    engine.start()

drive("Tesla")  # 输出：驾驶 Tesla 和 引擎启动

# 使用作用域管理依赖
with create_scope():
    provide('engine', Engine())  # 提供一个新的 Engine 实例
    drive("BMW")  # 输出：驾驶 BMW 和 引擎启动

# 在作用域之外，原始值得以保留
drive("Toyota")  # 输出：驾驶 Toyota 和 引擎启动
```

## API 参考

### `provide(key: str, value: Any, namespace: str = 'default')`

在当前上下文中提供一个依赖。

### `inject(key: str, namespace: str = 'default') -> Any`

从当前上下文中注入一个依赖。

### `create_scope()`

创建一个新的依赖作用域。与 `with` 语句一起使用。

### `scoped()`

为函数创建新的依赖作用域的装饰器。

### `auto_inject()`

自动注入被 `Inject` 标记的参数的装饰器。

### `Inject(key: str, namespace: str = 'default')`

标记一个参数应该被自动注入的类。

### `purge(namespace: Optional[str] = None)`

清除依赖，可以是特定命名空间的依赖或所有命名空间的依赖。


## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。