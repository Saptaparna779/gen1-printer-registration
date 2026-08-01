import pytest
from app import store


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()
