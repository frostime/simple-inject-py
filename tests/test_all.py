import pytest

from simple_inject import dependency_scope, inject, inject_scope, provide


@pytest.fixture(autouse=True)
def setup_global_config():
    provide('global_config', {'app_name': 'MyApp', 'version': '1.0'})
    yield
    # 清理全局配置（如果需要的话）


def test_simple():
    """
    测试 simple_inject 的基本功能，包括：
    1. 基本的 provide 和 inject 操作
    2. 默认命名空间的行为
    3. 显式指定命名空间的行为
    4. 错误处理（键不存在和命名空间不存在的情况）
    5. 默认命名空间和显式命名空间的交互
    """
    # 测试基本的 provide 和 inject 功能（使用默认命名空间）
    provide('key1', 'value1')
    assert inject('key1') == 'value1'

    # 测试默认命名空间
    provide('key2', 'value2')
    assert inject('key2') == 'value2'
    assert inject('key2', namespace='default') == 'value2'

    # 测试显式指定默认命名空间
    provide('key3', 'value3', namespace='default')
    assert inject('key3') == 'value3'

    # 测试不同命名空间
    provide('key4', 'value4', namespace='custom')
    assert inject('key4', namespace='custom') == 'value4'

    # 验证默认命名空间和自定义命名空间的隔离
    with pytest.raises(KeyError):
        inject('key4')  # 在默认命名空间中不应该找到 'key4'

    # 测试键不存在的情况
    with pytest.raises(KeyError):
        inject('non_existent_key')

    # 测试命名空间不存在的情况
    with pytest.raises(KeyError):
        inject('key1', namespace='non_existent_namespace')


def test_dependency_scope():
    """
    测试 dependency_scope 上下文管理器的功能，包括：
    1. 在作用域内提供和注入依赖
    2. 作用域结束后依赖的清理
    3. 默认命名空间和显式命名空间在作用域内的行为
    """
    with dependency_scope('test'):
        provide('db', 'test_db', namespace='test')
        assert inject('db', namespace='test') == 'test_db'

        # 测试在作用域内使用默认命名空间
        provide('default_key', 'default_value')
        assert inject('default_key') == 'default_value'

        assert inject('global_config')['app_name'] == 'MyApp'

    # 验证作用域结束后，依赖被清理
    with pytest.raises(KeyError):
        inject('db', namespace='test')

    # 验证默认命名空间的依赖也被清理
    with pytest.raises(KeyError):
        inject('default_key')


@inject_scope('production')
def production_function():
    provide('db', 'production_db', namespace='production')
    assert inject('db', namespace='production') == 'production_db'

    # 测试在装饰器作用域内使用默认命名空间
    provide('prod_default', 'prod_default_value')
    assert inject('prod_default') == 'prod_default_value'

    assert inject('global_config')['app_name'] == 'MyApp'


def test_inject_scope():
    """
    测试 inject_scope 装饰器的功能，包括：
    1. 装饰器作用域内的依赖注入
    2. 装饰器作用域结束后依赖的清理
    3. 默认命名空间和显式命名空间在装饰器作用域内的行为
    """
    production_function()

    # 验证装饰器作用域结束后，依赖被清理
    with pytest.raises(KeyError):
        inject('db', namespace='production')

    # 验证默认命名空间的依赖也被清理
    with pytest.raises(KeyError):
        inject('prod_default')


def test_global_config_persistence():
    """
    测试全局配置的持久性，确保它在所有测试中都可用
    """
    assert inject('global_config')['app_name'] == 'MyApp'


def test_multiple_namespaces():
    """
    测试多个嵌套的命名空间，包括：
    1. 不同命名空间之间的隔离
    2. 嵌套作用域中的依赖注入
    3. 作用域结束后各个命名空间中依赖的清理
    """
    with dependency_scope('namespace1'):
        provide('key', 'value1', namespace='namespace1')
        provide('default_key', 'default_value1')  # 使用默认命名空间
        with dependency_scope('namespace2'):
            provide('key', 'value2', namespace='namespace2')
            provide('default_key', 'default_value2')  # 覆盖默认命名空间的值
            assert inject('key', namespace='namespace1') == 'value1'
            assert inject('key', namespace='namespace2') == 'value2'
            assert inject('default_key') == 'default_value2'

        # 验证内层作用域结束后，外层作用域和默认命名空间的值仍然存在
        assert inject('key', namespace='namespace1') == 'value1'
        assert inject('default_key') == 'default_value1'

    # 验证所有作用域结束后，依赖被清理
    with pytest.raises(KeyError):
        inject('key', namespace='namespace1')
    with pytest.raises(KeyError):
        inject('key', namespace='namespace2')
    with pytest.raises(KeyError):
        inject('default_key')


def test_complex_nested_dependencies():
    """
    测试复杂的嵌套依赖关系，模拟真实的应用程序结构，包括：
    1. 多层嵌套的依赖作用域
    2. 跨作用域的依赖注入
    3. 默认命名空间和显式命名空间的混合使用
    4. 作用域结束后的依赖清理
    5. 全局配置的持久性
    """
    # 全局配置
    assert inject('global_config')['app_name'] == 'MyApp'
    assert inject('global_config')['version'] == '1.0'

    # 模拟数据库连接
    @inject_scope('database')
    def setup_database():
        provide(
            'db_connection', 'postgresql://localhost:5432/myapp', namespace='database'
        )
        provide('db_pool_size', 10, namespace='database')
        provide('default_db_config', {'timeout': 30})  # 使用默认命名空间

        # 模拟用户服务
        with dependency_scope('user_service'):
            provide('user_table', 'users', namespace='user_service')
            provide('user_cache', {}, namespace='user_service')
            provide('default_user_config', {'max_users': 1000})  # 使用默认命名空间

            # 模拟认证服务
            @inject_scope('auth_service')
            def setup_auth_service():
                provide('auth_secret', 'super_secret_key', namespace='auth_service')
                provide('token_expiration', 3600, namespace='auth_service')
                provide('default_auth_config', {'algorithm': 'HS256'})  # 使用默认命名空间

                # 验证嵌套的依赖注入
                assert (
                    inject('db_connection', namespace='database')
                    == 'postgresql://localhost:5432/myapp'
                )
                assert inject('user_table', namespace='user_service') == 'users'
                assert (
                    inject('auth_secret', namespace='auth_service') == 'super_secret_key'
                )
                assert inject('default_db_config')['timeout'] == 30
                assert inject('default_user_config')['max_users'] == 1000
                assert inject('default_auth_config')['algorithm'] == 'HS256'

                # 模拟一个需要多个依赖的复杂函数
                def complex_auth_function():
                    db = inject('db_connection', namespace='database')
                    user_cache = inject('user_cache', namespace='user_service')
                    auth_secret = inject('auth_secret', namespace='auth_service')
                    global_config = inject('global_config')
                    default_auth_config = inject('default_auth_config')

                    return f"Auth function using {db}, {user_cache}, {auth_secret}, {global_config['app_name']}, and {default_auth_config['algorithm']}"

                result = complex_auth_function()
                assert 'Auth function using postgresql://localhost:5432/myapp' in result
                assert 'super_secret_key' in result
                assert 'MyApp' in result
                assert 'HS256' in result

            setup_auth_service()

            # 验证 auth_service 作用域已经结束
            with pytest.raises(KeyError):
                inject('auth_secret', namespace='auth_service')
            with pytest.raises(KeyError):
                inject('default_auth_config')

        # 验证 user_service 作用域已经结束
        with pytest.raises(KeyError):
            inject('user_table', namespace='user_service')
        with pytest.raises(KeyError):
            inject('default_user_config')

    setup_database()

    # 验证 database 作用域已经结束
    with pytest.raises(KeyError):
        inject('db_connection', namespace='database')
    with pytest.raises(KeyError):
        inject('default_db_config')

    # 全局配置仍然可用
    assert inject('global_config')['app_name'] == 'MyApp'
