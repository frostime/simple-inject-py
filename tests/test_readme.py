# tests/test_readme_examples.py

import pytest

from simple_inject import dependency_scope, inject, inject_scope, provide


def test_basic_usage():
    # Provide a dependency
    provide('config', {'api_key': 'abc123'})

    # Inject a dependency
    config = inject('config')
    assert config['api_key'] == 'abc123'


def test_using_namespaces():
    # Provide dependencies in different namespaces
    provide('db', 'production_db', namespace='production')
    provide('db', 'test_db', namespace='test')

    # Inject dependencies from specific namespaces
    prod_db = inject('db', namespace='production')
    test_db = inject('db', namespace='test')

    assert prod_db == 'production_db'
    assert test_db == 'test_db'


def test_using_scopes():
    with dependency_scope('request'):
        provide('user', {'id': 1, 'name': 'Alice'})
        user = inject('user')
        assert user['name'] == 'Alice'

    # The "user" dependency is no longer available outside the scope
    with pytest.raises(KeyError):
        inject('user')


def test_inject_scope_decorator():
    @inject_scope('session')
    def process_user():
        provide('session_id', '123456')
        session_id = inject('session_id')
        return f'Processing user with session ID: {session_id}'

    result = process_user()
    assert result == 'Processing user with session ID: 123456'

    # The "session_id" dependency is no longer available after the function call
    with pytest.raises(KeyError):
        inject('session_id')


def test_nested_scopes():
    provide('global_var', 'I am global')

    with dependency_scope('outer'):
        provide('outer_var', 'I am outer')

        assert inject('global_var') == 'I am global'
        assert inject('outer_var') == 'I am outer'

        with dependency_scope('inner'):
            provide('inner_var', 'I am inner')

            assert inject('global_var') == 'I am global'
            assert inject('outer_var') == 'I am outer'
            assert inject('inner_var') == 'I am inner'

        assert inject('global_var') == 'I am global'
        assert inject('outer_var') == 'I am outer'
        with pytest.raises(KeyError):
            inject('inner_var')

    assert inject('global_var') == 'I am global'
    with pytest.raises(KeyError):
        inject('outer_var')
    with pytest.raises(KeyError):
        inject('inner_var')


def test_overriding_dependencies():
    provide('config', {'env': 'production'})
    assert inject('config')['env'] == 'production'

    with dependency_scope('test'):
        provide('config', {'env': 'test'})
        assert inject('config')['env'] == 'test'

    assert inject('config')['env'] == 'production'


def test_default_namespace():
    provide('default_key', 'default_value')
    provide('custom_key', 'custom_value', namespace='custom')

    assert inject('default_key') == 'default_value'
    assert inject('custom_key', namespace='custom') == 'custom_value'

    with pytest.raises(KeyError):
        inject('custom_key')  # This should fail as it's not in the default namespace


if __name__ == '__main__':
    pytest.main()
