from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.api import app
from src.auth import hash_password
from src.db import create_user_with_password


def _client_for(email: str, password: str) -> TestClient:
    client = TestClient(app)
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return client


def test_users_only_see_own_medications_and_schedules():
    create_user_with_password("alice@test.pi11box", "Alice", hash_password("secret123"))
    create_user_with_password("bob@test.pi11box", "Bob", hash_password("secret123"))

    alice = _client_for("alice@test.pi11box", "secret123")
    alice_med = alice.post("/medications", json={"name": "Аспирин Alice"})
    assert alice_med.status_code == 201
    alice_med_id = alice_med.json()["id"]

    intake_at = datetime.now(timezone.utc) + timedelta(hours=1)
    alice_schedule = alice.post(
        f"/medications/{alice_med_id}/schedules",
        json={"intake_at": intake_at.isoformat(), "dose": "1 таб"},
    )
    assert alice_schedule.status_code == 201

    bob = _client_for("bob@test.pi11box", "secret123")
    bob_med = bob.post("/medications", json={"name": "Ибупрофен Bob"})
    assert bob_med.status_code == 201

    alice_meds = alice.get("/medications")
    assert alice_meds.status_code == 200
    assert {m["name"] for m in alice_meds.json()} == {"Аспирин Alice"}

    bob_meds = bob.get("/medications")
    assert bob_meds.status_code == 200
    assert {m["name"] for m in bob_meds.json()} == {"Ибупрофен Bob"}

    bob_cannot_see_alice_med = bob.get(f"/medications/{alice_med_id}")
    assert bob_cannot_see_alice_med.status_code == 404

    bob_cannot_see_alice_schedules = bob.get(f"/medications/{alice_med_id}/schedules")
    assert bob_cannot_see_alice_schedules.status_code == 404
