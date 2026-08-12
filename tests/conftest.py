import pytest
from fastapi.testclient import TestClient
from app import store
from app.main import app
from app.auth import create_access_token


@pytest.fixture(autouse=True)
def reset_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture
def client():
    test_client = TestClient(app)
    token = create_access_token(subject="test-user")
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client
