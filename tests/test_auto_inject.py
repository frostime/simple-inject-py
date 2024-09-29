import pytest  # Added import for pytest

from simple_inject import Inject, auto_inject, create_scope, inject, provide


class Engine:
    def start(self):
        print('Engine started')


class InjectEngine(Inject[Engine]):
    def __init__(self):
        super().__init__('engine')


@auto_inject()
def f1(arg1, arg2, *, engine: InjectEngine):
    engine.start()
    print(f'f1 called with {arg1}, {arg2}')


@auto_inject()
def f2(arg1, arg2, engine: Engine = Inject('engine')):
    engine.start()
    print(f'f2 called with {arg1}, {arg2}')


@pytest.fixture  # Added pytest fixture for setup
def setup_engine():
    provide('engine', Engine())  # Provide engine for tests
    yield  # This allows the test to run
    # Cleanup can be added here if necessary


def test_f1(setup_engine):  # Test for f1
    f1('hello', 'world')  # You can add assertions as needed


def test_f2(setup_engine):  # Test for f2
    f2('foo', 'bar')  # You can add assertions as needed
