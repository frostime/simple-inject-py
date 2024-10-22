import pytest

from simple_inject import create_scope, inject, provide, purge, scoped, update


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    # Setup: Provide a global configuration
    provide('global_config', {'app_name': 'MyApp', 'version': '1.0'})
    yield
    # Cleanup: Purge all dependencies after each test
    purge()


def test_provide_and_inject_basic():
    """
    Test basic provide and inject functionality in the default namespace.
    """
    provide('key', 'value')
    assert inject('key') == 'value'


def test_provide_and_inject_with_namespace():
    """
    Test provide and inject functionality with explicit namespaces.
    """
    provide('key', 'value1', namespace='ns1')
    provide('key', 'value2', namespace='ns2')
    assert inject('key', namespace='ns1') == 'value1'
    assert inject('key', namespace='ns2') == 'value2'


def test_inject_nonexistent_key():
    """
    Test that injecting a non-existent key raises a DependencyNotFoundError.
    """
    with pytest.raises(Exception):  # Replace with the actual exception class if known
        inject('nonexistent_key', if_not_found='raise')


def test_create_scope():
    """
    Test that create_scope creates an isolated scope for dependencies.
    """
    provide('key', 'outer_value')
    with create_scope():
        provide('key', 'inner_value')
        assert inject('key') == 'inner_value'
    assert inject('key') == 'outer_value'


def test_nested_scopes():
    """
    Test that nested scopes work correctly.
    """
    provide('key', 'outer_value')
    with create_scope():
        provide('key', 'middle_value')
        with create_scope():
            provide('key', 'inner_value')
            assert inject('key') == 'inner_value'
        assert inject('key') == 'middle_value'
    assert inject('key') == 'outer_value'


def test_scoped_decorator():
    """
    Test that the scoped decorator creates an isolated scope for a function.
    """
    provide('key', 'outer_value')

    @scoped()
    def scoped_function():
        provide('key', 'inner_value')
        assert inject('key') == 'inner_value'

    scoped_function()
    assert inject('key') == 'outer_value'


def test_multiple_namespaces_in_scope():
    """
    Test that different namespaces are isolated within the same scope.
    """
    provide('key', 'value1', namespace='ns1')
    provide('key', 'value2', namespace='ns2')
    with create_scope():
        provide('key', 'new_value1', namespace='ns1')
        assert inject('key', namespace='ns1') == 'new_value1'
        assert inject('key', namespace='ns2') == 'value2'


def test_purge_specific_namespace():
    """
    Test that purging a specific namespace works correctly.
    """
    provide('key1', 'value1', namespace='ns1')
    provide('key2', 'value2', namespace='ns2')
    purge(namespace='ns1')
    with pytest.raises(Exception):
        inject('key1', namespace='ns1', if_not_found='raise')
    assert inject('key2', namespace='ns2') == 'value2'


def test_purge_all():
    """
    Test that purging all namespaces works correctly.
    """
    provide('key1', 'value1', namespace='ns1')
    provide('key2', 'value2', namespace='ns2')
    purge()
    with pytest.raises(Exception):
        inject('key1', namespace='ns1', if_not_found='raise')
    with pytest.raises(Exception):
        inject('key2', namespace='ns2', if_not_found='raise')


def test_global_config_fixture():
    """
    Test that the global_config provided by the fixture is accessible.
    """
    config = inject('global_config')
    assert config['app_name'] == 'MyApp'
    assert config['version'] == '1.0'


def test_provide_overwrites_existing_value():
    """
    Test that providing a value for an existing key overwrites the old value.
    """
    provide('key', 'old_value')
    provide('key', 'new_value')
    assert inject('key') == 'new_value'


def test_scope_isolation_between_tests():
    """
    Test that dependencies are isolated between test functions.
    This test relies on the purge() call in the cleanup fixture.
    """
    with pytest.raises(Exception):
        inject('key_from_previous_test', if_not_found='raise')
    provide('key_for_next_test', 'value')


def test_update():
    """
    Test the update functionality.
    """
    provide('counter', 0)
    assert inject('counter') == 0

    def increment(x):
        return x + 1

    update('counter', increment)
    assert inject('counter') == 1

    update('counter', lambda x: x * 2)
    assert inject('counter') == 2

    # Test update with namespace
    provide('counter', 10, namespace='ns1')
    update('counter', increment, namespace='ns1')
    assert inject('counter', namespace='ns1') == 11
    assert inject('counter') == 2  # Ensure default namespace is unchanged

    # Test update on non-existent key
    with pytest.raises(Exception):
        update('non_existent', increment)
