import os

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "postgresql://pillbox_test:pillbox_test@localhost:5433/pillbox_test"

database_url = os.environ.get("DATABASE_URL", TEST_DATABASE_URL)
if "pillbox_test" not in database_url:
    pytest.exit(
        "Отказ: тесты нельзя запускать на продакшен-БД. "
        f"DATABASE_URL={database_url!r}. Используйте ./scripts/run_tests.sh"
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("SESSION_COOKIE_PATH", "/")
os.environ.setdefault("SCHEDULER_GRACE_MINUTES", "1")
os.environ.setdefault("SCHEDULER_MAX_REMINDERS", "3")

from src import auth
from src.api import app
from src.db_init import init_database
from src.seed_data import reset_test_data, seed_demo_data


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    auth.SESSION_COOKIE_PATH = "/"
    init_database()
    yield


@pytest.fixture(autouse=True)
def clean_db():
    reset_test_data()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def seeded():
    return seed_demo_data()


@pytest.fixture
def auth_client(client, seeded):
    response = client.post(
        "/auth/login",
        json={"email": "patient@test.pi11box", "password": "testpass123"},
    )
    assert response.status_code == 200
    return client
