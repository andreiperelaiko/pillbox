from fastapi.testclient import TestClient

from src.api import app
from src.auth import hash_password
from src.db import (
    accept_guardian_invite,
    create_user_with_password,
    get_guardian_invites_to_notify,
    guardian_link_exists,
    respond_to_guardian_invite,
    save_telegram_chat_id,
)


def _client_for(email: str, password: str = "secret123") -> TestClient:
    client = TestClient(app)
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return client


def test_guardian_attach_flow(client):
    patient_id = create_user_with_password(
        "patient_guardian@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="patient_g",
    )
    guardian_id = create_user_with_password(
        "guardian_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="guardian_g",
    )
    save_telegram_chat_id(patient_id, "111110")
    save_telegram_chat_id(guardian_id, "111111")

    guardian = _client_for("guardian_guardian@test.pi11box")

    lookup = guardian.get("/users/email/patient_guardian@test.pi11box")
    assert lookup.status_code == 200
    assert lookup.json()["id"] == patient_id

    attach = guardian.post(
        f"/guardians/attach/{patient_id}",
        json={"relationship": "дочь"},
    )
    assert attach.status_code == 202
    invite_id = attach.json()["id"]
    assert attach.json()["status"] == "pending"

    assert guardian.get("/wards").json() == []

    assert accept_guardian_invite(invite_id, guardian_id)

    wards = guardian.get("/wards")
    assert wards.status_code == 200
    assert len(wards.json()) == 1
    assert wards.json()[0]["email"] == "patient_guardian@test.pi11box"

    patient = _client_for("patient_guardian@test.pi11box")
    guardians = patient.get("/guardians")
    assert guardians.status_code == 200
    assert len(guardians.json()) == 1
    assert guardians.json()[0]["email"] == "guardian_guardian@test.pi11box"

    removed = guardian.delete(f"/wards/{patient_id}")
    assert removed.status_code == 204
    assert guardian.get("/wards").json() == []


def test_guardian_initiator_cannot_approve(client):
    patient_id = create_user_with_password(
        "both_patient@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="both_patient",
    )
    guardian_id = create_user_with_password(
        "both_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="both_guardian",
    )
    save_telegram_chat_id(patient_id, "444441")

    guardian = _client_for("both_guardian@test.pi11box")
    attach = guardian.post(
        f"/guardians/attach/{patient_id}",
        json={"relationship": "сестра"},
    )
    assert attach.status_code == 202
    invite_id = attach.json()["id"]

    assert respond_to_guardian_invite(invite_id, guardian_id, True) == "not_approver"
    assert not guardian_link_exists(patient_id, guardian_id)
    assert guardian.get("/wards").json() == []

    assert respond_to_guardian_invite(invite_id, patient_id, True) == "completed"
    assert guardian_link_exists(patient_id, guardian_id)
    assert len(guardian.get("/wards").json()) == 1


def test_patient_initiator_cannot_approve(client):
    patient_id = create_user_with_password(
        "invite_only_patient@test.pi11box",
        "Пациент",
        hash_password("secret123"),
    )
    guardian_id = create_user_with_password(
        "invite_only_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="invite_only_guardian",
    )
    save_telegram_chat_id(guardian_id, "555552")

    patient = _client_for("invite_only_patient@test.pi11box")
    invite = patient.post(
        "/guardians/invite",
        json={"email": "invite_only_guardian@test.pi11box", "relationship": "мать"},
    )
    assert invite.status_code == 202
    invite_id = invite.json()["id"]

    assert respond_to_guardian_invite(invite_id, patient_id, True) == "not_approver"
    assert not guardian_link_exists(patient_id, guardian_id)

    assert respond_to_guardian_invite(invite_id, guardian_id, True) == "completed"
    assert guardian_link_exists(patient_id, guardian_id)


def test_guardian_reattach_after_remove_creates_pending_invite(client):
    patient_id = create_user_with_password(
        "reattach_patient@test.pi11box",
        "Пациент",
        hash_password("secret123"),
        telegram="reattach_patient",
    )
    guardian_id = create_user_with_password(
        "reattach_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="reattach_guardian",
    )
    save_telegram_chat_id(patient_id, "333331")
    save_telegram_chat_id(guardian_id, "333332")

    guardian = _client_for("reattach_guardian@test.pi11box")
    attach = guardian.post(
        f"/guardians/attach/{patient_id}",
        json={"relationship": "брат"},
    )
    assert attach.status_code == 202
    invite_id = attach.json()["id"]
    assert accept_guardian_invite(invite_id, guardian_id)

    assert guardian.delete(f"/wards/{patient_id}").status_code == 204

    reattach = guardian.post(
        f"/guardians/attach/{patient_id}",
        json={"relationship": "брат"},
    )
    assert reattach.status_code == 202
    assert reattach.json()["status"] == "pending"

    pending = get_guardian_invites_to_notify()
    assert any(item["id"] == reattach.json()["id"] for item in pending)
    assert guardian.get("/wards").json() == []


def test_guardian_invite_by_email(client):
    patient_id = create_user_with_password(
        "invite_patient@test.pi11box",
        "Пациент",
        hash_password("secret123"),
    )
    guardian_id = create_user_with_password(
        "invite_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="invite_g",
    )
    save_telegram_chat_id(patient_id, "222221")
    save_telegram_chat_id(guardian_id, "222222")

    patient = _client_for("invite_patient@test.pi11box")
    invite = patient.post(
        "/guardians/invite",
        json={"email": "invite_guardian@test.pi11box", "relationship": "сын"},
    )
    assert invite.status_code == 202
    invite_id = invite.json()["id"]

    assert patient.get("/guardians").json() == []
    assert accept_guardian_invite(invite_id, guardian_id)

    guardians = patient.get("/guardians")
    assert len(guardians.json()) == 1
    assert guardians.json()[0]["email"] == "invite_guardian@test.pi11box"

    guardian = _client_for("invite_guardian@test.pi11box")
    assert len(guardian.get("/wards").json()) == 1
    assert guardian.get("/wards").json()[0]["id"] == patient_id


def test_guardian_attach_requires_telegram(client):
    patient_id = create_user_with_password(
        "patient_notg@test.pi11box",
        "Пациент",
        hash_password("secret123"),
    )
    create_user_with_password(
        "guardian_notg@test.pi11box",
        "Опекун",
        hash_password("secret123"),
        telegram="no_chat",
    )

    guardian = _client_for("guardian_notg@test.pi11box")
    attach = guardian.post(f"/guardians/attach/{patient_id}", json={})
    assert attach.status_code == 400


def test_user_lookup_case_insensitive(client):
    create_user_with_password(
        "CaseTest@test.pi11box",
        "Case",
        hash_password("secret123"),
    )
    create_user_with_password(
        "lookup_guardian@test.pi11box",
        "Опекун",
        hash_password("secret123"),
    )
    guardian = _client_for("lookup_guardian@test.pi11box")
    response = guardian.get("/users/email/casetest@test.pi11box")
    assert response.status_code == 200
