def test_register_login_and_me(client):
    register = client.post(
        "/auth/register",
        json={
            "email": "newuser@test.pi11box",
            "name": "Новый пользователь",
            "password": "secret123",
        },
    )
    assert register.status_code == 201
    assert register.json()["email"] == "newuser@test.pi11box"

    login = client.post(
        "/auth/login",
        json={"email": "newuser@test.pi11box", "password": "secret123"},
    )
    assert login.status_code == 200

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["name"] == "Новый пользователь"


def test_login_invalid_password(client, seeded):
    response = client.post(
        "/auth/login",
        json={"email": "patient@test.pi11box", "password": "wrong"},
    )
    assert response.status_code == 401


def test_protected_route_requires_auth(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout_clears_session(auth_client):
    response = auth_client.post("/auth/logout")
    assert response.status_code == 200
    assert auth_client.get("/auth/me").status_code == 401
