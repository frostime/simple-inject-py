import pytest

from simple_inject import create_scope, inject, provide, purge, scoped


@pytest.fixture(autouse=True)
def clear_dependencies():
    yield
    purge()


def test_basic_provide_and_inject():
    """测试基本的 provide 和 inject 功能"""
    provide('config', {'debug': True})
    config = inject('config')
    assert config['debug'] is True


def test_scope_management():
    """测试使用作用域管理依赖"""
    provide('config', {'debug': True})

    with create_scope():
        provide('config', {'debug': False})
        config = inject('config')
        assert config['debug'] is False

    config = inject('config')
    assert config['debug'] is True


def test_namespaces():
    """测试使用命名空间"""
    provide('key', 'value1', namespace='ns1')
    provide('key', 'value2', namespace='ns2')

    assert inject('key', namespace='ns1') == 'value1'
    assert inject('key', namespace='ns2') == 'value2'


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


@scoped()
def scoped_function():
    provide('key', 'scoped_value')
    return inject('key')


def test_scoped_decorator():
    """测试 scoped 装饰器"""
    provide('key', 'outer_value')

    assert scoped_function() == 'scoped_value'
    assert inject('key') == 'outer_value'


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
