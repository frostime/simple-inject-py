import pytest

from simple_inject import (
    Inject,
    auto_inject,
    create_scope,
    inject,
    provide,
    purge,
    scoped,
)


@pytest.fixture(autouse=True)
def clear_dependencies():
    yield
    purge()


def test_basic_provide_and_inject():
    """测试基本的 provide 和 inject 功能"""
    provide('config', {'debug': True})
    config = inject('config')
    assert config['debug'] is True


def test_namespaces():
    """测试使用命名空间"""
    provide('key', 'value1', namespace='ns1')
    provide('key', 'value2', namespace='ns2')

    assert inject('key', namespace='ns1') == 'value1'
    assert inject('key', namespace='ns2') == 'value2'


def test_scope_management():
    """测试使用作用域管理依赖"""
    provide('config', {'debug': True})

    with create_scope():
        provide('config', {'debug': False})
        config = inject('config')
        assert config['debug'] is False

    config = inject('config')
    assert config['debug'] is True


@scoped()
def scoped_function():
    provide('key', 'scoped_value')
    return inject('key')


def test_scoped_decorator():
    """测试 scoped 装饰器"""
    provide('key', 'outer_value')

    assert inject('key') == 'outer_value'
    assert scoped_function() == 'scoped_value'
    assert inject('key') == 'outer_value'


def test_nested_scopes():
    """测试嵌套作用域"""
    provide('key', 'outer')

    with create_scope():
        provide('key', 'inner')
        assert inject('key') == 'inner'

        with create_scope():
            provide('key', 'innermost')
            assert inject('key') == 'innermost'

        assert inject('key') == 'inner'

    assert inject('key') == 'outer'


class Engine:
    def __init__(self, id: str):
        self.id = id

    def start(self):
        # print('Engine started')
        return f'引擎 {self.id} 启动'


class InjectEngine(Inject[Engine]):
    def __init__(self):
        super().__init__('engine')


# 使用自动注入
@auto_inject()
def drive(car: str, engine: Engine = Inject('engine')):
    tip = f'驾驶 {car}: {engine.start()}'
    print(tip)
    return tip


def test_auto_inject():
    provide('engine', Engine(1))
    assert drive('Tesla') == '驾驶 Tesla: 引擎 1 启动'
    assert drive('BMW') == '驾驶 BMW: 引擎 1 启动'

    with create_scope():
        provide('engine', Engine(2))
        assert drive('Tesla') == '驾驶 Tesla: 引擎 2 启动'
        assert drive('BMW') == '驾驶 BMW: 引擎 2 启动'

    assert drive('Tesla') == '驾驶 Tesla: 引擎 1 启动'
    assert drive('BMW') == '驾驶 BMW: 引擎 1 启动'


def test_purge():
    """测试 purge 功能"""
    provide('key1', 'value1', namespace='ns1')
    provide('key2', 'value2', namespace='ns2')

    purge('ns1')
    with pytest.raises(Exception):
        inject('key1', namespace='ns1')
    assert inject('key2', namespace='ns2') == 'value2'

    provide('key1', 'new_value1', namespace='ns1')
    purge()
    with pytest.raises(Exception):
        inject('key1', namespace='ns1')
    with pytest.raises(Exception):
        inject('key2', namespace='ns2')


if __name__ == '__main__':
    pytest.main(['-v', __file__])
