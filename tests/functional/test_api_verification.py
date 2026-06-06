from src.db import create_email_verification_token, get_auth_user_by_email


def test_settings_endpoint(auth_client, seeded):
    settings = auth_client.get("/auth/settings")
    assert settings.status_code == 200
    body = settings.json()
    assert body["email"] == "patient@test.pi11box"
    assert body["email_verified"] is False
    assert body["telegram_bot_url"].startswith("https://t.me/")


def test_send_email_verification(auth_client, seeded):
    response = auth_client.post("/auth/verification/email/send")
    assert response.status_code == 200
    assert "message" in response.json()


def test_email_verification_confirm(auth_client, seeded):
    user = get_auth_user_by_email("patient@test.pi11box")
    token = create_email_verification_token(user["id"])

    confirm = auth_client.get(
        f"/auth/verification/email/confirm?token={token}",
        follow_redirects=False,
    )
    assert confirm.status_code == 302
    assert "email_verified=1" in confirm.headers["location"]

    settings = auth_client.get("/auth/settings")
    assert settings.json()["email_verified"] is True


def test_update_telegram_profile(auth_client, seeded):
    response = auth_client.patch("/auth/profile", json={"telegram": "@test_patient"})
    assert response.status_code == 200
    assert response.json()["telegram"] == "test_patient"
    assert response.json()["telegram_verified"] is False


def test_telegram_username_must_be_unique(client, seeded):
    taken = client.post(
        "/auth/register",
        json={
            "email": "telegram_dup@test.pi11box",
            "name": "Дубликат",
            "password": "secret123",
            "telegram": "@test_guardian",
        },
    )
    assert taken.status_code == 400
    assert "Telegram" in taken.json()["detail"]

    other = client.post(
        "/auth/register",
        json={
            "email": "telegram_ok@test.pi11box",
            "name": "Уникальный",
            "password": "secret123",
            "telegram": "@unique_user_123",
        },
    )
    assert other.status_code == 201
    assert other.json()["telegram"] == "unique_user_123"

    login = client.post(
        "/auth/login",
        json={"email": "patient@test.pi11box", "password": "testpass123"},
    )
    assert login.status_code == 200

    conflict = client.patch("/auth/profile", json={"telegram": "@test_guardian"})
    assert conflict.status_code == 400
    assert "Telegram" in conflict.json()["detail"]
