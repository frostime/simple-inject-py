import pytest

from simple_inject import create_scope, provide, inject, purge


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    # Setup: Clean state
    purge()
    yield
    # Cleanup: Purge all dependencies after each test
    purge()


def test_scoped_state_provided_policy():
    """Test scoped_state with 'Provided' policy - only new/modified dependencies"""
    # Setup initial state
    provide('existing_key', 'initial_value')
    provide('another_key', 'another_initial')

    with create_scope() as scope:
        # Modify existing dependency
        provide('existing_key', 'modified_value')
        # Add new dependency
        provide('new_key', 'new_value')
        # Keep one dependency unchanged
        assert inject('another_key') == 'another_initial'

    # Test 'Provided' policy (default)
    provided_state = scope.scoped_state()
    expected = {'default': {'existing_key': 'modified_value', 'new_key': 'new_value'}}
    assert provided_state == expected

    # Test explicit 'Provided' policy
    provided_state_explicit = scope.scoped_state('Provided')
    assert provided_state_explicit == expected


def test_scoped_state_all_policy():
    """Test scoped_state with 'All' policy - complete scope state"""
    # Setup initial state
    provide('existing_key', 'initial_value')
    provide('another_key', 'another_initial')

    with create_scope() as scope:
        provide('existing_key', 'modified_value')
        provide('new_key', 'new_value')

    # Test 'All' policy
    all_state = scope.scoped_state('All')
    expected = {
        'default': {
            'existing_key': 'modified_value',
            'new_key': 'new_value',
            'another_key': 'another_initial',
        }
    }
    assert all_state == expected


def test_scoped_state_with_namespace():
    """Test scoped_state with specific namespace"""
    # Setup initial state in multiple namespaces
    provide('key1', 'value1', namespace='ns1')
    provide('key2', 'value2', namespace='ns2')

    with create_scope() as scope:
        provide('key1', 'modified1', namespace='ns1')
        provide('new_key', 'new_value', namespace='ns1')
        provide('key3', 'value3', namespace='ns2')

    # Test specific namespace with 'Provided' policy
    ns1_provided = scope.scoped_state('Provided', 'ns1')
    expected_ns1 = {'key1': 'modified1', 'new_key': 'new_value'}
    assert ns1_provided == expected_ns1

    # Test specific namespace with 'All' policy
    ns1_all = scope.scoped_state('All', 'ns1')
    assert ns1_all == expected_ns1

    # Test namespace that has only new dependencies
    ns2_provided = scope.scoped_state('Provided', 'ns2')
    expected_ns2 = {'key3': 'value3'}
    assert ns2_provided == expected_ns2


def test_scoped_state_empty_scope():
    """Test scoped_state when no changes were made in scope"""
    provide('existing_key', 'value')

    with create_scope() as scope:
        # No changes made in scope
        assert inject('existing_key') == 'value'

    # Should return empty dict for 'Provided' policy
    provided_state = scope.scoped_state('Provided')
    assert provided_state == {}

    # Should return inherited state for 'All' policy
    all_state = scope.scoped_state('All')
    expected = {'default': {'existing_key': 'value'}}
    assert all_state == expected


def test_scoped_state_nested_scopes():
    """Test scoped_state with nested scopes"""
    provide('key', 'initial')

    with create_scope() as outer_scope:
        provide('key', 'outer_modified')
        provide('outer_key', 'outer_value')

        with create_scope() as inner_scope:
            provide('key', 'inner_modified')
            provide('inner_key', 'inner_value')

        # Inner scope should only show its changes
        inner_provided = inner_scope.scoped_state('Provided')
        expected_inner = {
            'default': {'key': 'inner_modified', 'inner_key': 'inner_value'}
        }
        assert inner_provided == expected_inner

    # Outer scope should show its changes
    outer_provided = outer_scope.scoped_state('Provided')
    expected_outer = {'default': {'key': 'outer_modified', 'outer_key': 'outer_value'}}
    assert outer_provided == expected_outer


def test_scoped_state_nonexistent_namespace():
    """Test scoped_state with non-existent namespace"""
    with create_scope() as scope:
        provide('key', 'value')

    # Should return empty dict for non-existent namespace
    result = scope.scoped_state('Provided', 'nonexistent')
    assert result == {}

    result_all = scope.scoped_state('All', 'nonexistent')
    assert result_all == {}


def test_scoped_state_before_exit_error():
    """Test that scoped_state raises error when called before exiting scope"""
    with pytest.raises(
        RuntimeError, match='scoped_state can only be called after exiting the scope'
    ):
        with create_scope() as scope:
            provide('key', 'value')
            scope.scoped_state()  # This should raise an error


def test_scoped_state_multiple_namespaces():
    """Test scoped_state with multiple namespaces"""
    # Setup initial state
    provide('key1', 'value1', namespace='ns1')
    provide('key2', 'value2', namespace='ns2')

    with create_scope() as scope:
        provide('key1', 'modified1', namespace='ns1')
        provide('new_key1', 'new_value1', namespace='ns1')
        provide('new_key2', 'new_value2', namespace='ns2')

    # Test all namespaces with 'Provided' policy
    all_provided = scope.scoped_state('Provided')
    expected = {
        'ns1': {'key1': 'modified1', 'new_key1': 'new_value1'},
        'ns2': {'new_key2': 'new_value2'},
    }
    assert all_provided == expected


def test_scoped_state_deep_copy():
    """Test scoped_state with deep copy option"""
    # Test with mutable objects
    provide('config', {'debug': True, 'features': ['a', 'b']})

    with create_scope(deep=True) as scope:
        config = inject('config')
        config['debug'] = False
        config['features'].append('c')
        provide('config', config)
        provide('new_config', {'new': True})

    provided_state = scope.scoped_state('Provided')
    expected = {
        'default': {
            'config': {'debug': False, 'features': ['a', 'b', 'c']},
            'new_config': {'new': True},
        }
    }
    assert provided_state == expected


def test_scoped_state_complex_nesting():
    """Test scoped_state with complex nested scope scenarios"""
    provide('global_key', 'global_value')

    with create_scope() as level1:
        provide('global_key', 'level1_modified')
        provide('level1_key', 'level1_value')

        with create_scope() as level2:
            provide('global_key', 'level2_modified')
            provide('level2_key', 'level2_value')

            with create_scope() as level3:
                provide('level3_key', 'level3_value')
                # Don't modify global_key in level3

            # Level3 should only show its own additions
            level3_state = level3.scoped_state('Provided')
            assert level3_state == {'default': {'level3_key': 'level3_value'}}

        # Level2 should show its changes
        level2_state = level2.scoped_state('Provided')
        expected_level2 = {
            'default': {'global_key': 'level2_modified', 'level2_key': 'level2_value'}
        }
        assert level2_state == expected_level2

    # Level1 should show its changes
    level1_state = level1.scoped_state('Provided')
    expected_level1 = {
        'default': {'global_key': 'level1_modified', 'level1_key': 'level1_value'}
    }
    assert level1_state == expected_level1


def test_scoped_state_copy_consistency():
    """Test that scoped_state respects the deep_copy parameter consistently"""
    # Test with mutable object
    original_list = ['a', 'b']
    provide('mutable_data', original_list)

    # Test deep copy behavior
    with create_scope(deep=True) as deep_scope:
        new_list = ['a', 'b', 'deep']
        provide('mutable_data', new_list)
        provide('immutable_data', 'deep_value')

    # Test shallow copy behavior
    with create_scope(deep=False) as shallow_scope:
        new_list = ['a', 'b', 'shallow']
        provide('mutable_data', new_list)
        provide('immutable_data', 'shallow_value')

    # Both should accurately capture what was provided
    deep_state = deep_scope.scoped_state('Provided')
    shallow_state = shallow_scope.scoped_state('Provided')

    # Verify the stored values match what was provided
    assert deep_state['default']['mutable_data'] == ['a', 'b', 'deep']
    assert deep_state['default']['immutable_data'] == 'deep_value'

    assert shallow_state['default']['mutable_data'] == ['a', 'b', 'shallow']
    assert shallow_state['default']['immutable_data'] == 'shallow_value'


def test_scoped_state_mutation_isolation():
    """Test that mutations after provide don't affect scoped_state results"""
    with create_scope(deep=True) as scope:
        mutable_obj = {'count': 0, 'items': []}
        provide('config', mutable_obj)

        # Mutate the object after providing it
        mutable_obj['count'] = 999
        mutable_obj['items'].append('should_not_appear')

    # The scoped_state should reflect the state at provide time, not after mutation
    state = scope.scoped_state('Provided')
    assert state['default']['config']['count'] == 0
    assert state['default']['config']['items'] == []
