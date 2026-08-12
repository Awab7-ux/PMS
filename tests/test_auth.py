import pytest

from backend.app import create_app, db


@pytest.fixture()
def app():
    app = create_app("testing")
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_user_success(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new.user@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["user"]["email"] == "new.user@example.com"
    assert "password" not in payload["data"]["user"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "new.user@example.com", "password": "StrongPassword123!"},
    )
    token = login_response.get_json()["data"]["access_token"]
    orgs_response = client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
    )
    orgs = orgs_response.get_json()["data"]
    assert isinstance(orgs, list)
    assert len(orgs) == 1
    assert orgs[0]["slug"] == "newuser"


def test_register_duplicate_email(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "username": "dupuser",
            "full_name": "Dup User",
            "password": "StrongPassword123!",
        },
    )
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "dup@example.com",
            "username": "another",
            "full_name": "Dup User",
            "password": "StrongPassword123!",
        },
    )
    assert response.status_code == 409


def test_register_weak_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@example.com",
            "username": "weakuser",
            "full_name": "Weak User",
            "password": "weak",
        },
    )
    assert response.status_code == 422


def test_login_success(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "full_name": "Login User",
            "password": "StrongPassword123!",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "StrongPassword123!"},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["data"]["access_token"]
    assert payload["data"]["refresh_token"]


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "username": "wronguser",
            "full_name": "Wrong User",
            "password": "StrongPassword123!",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "IncorrectPassword!"},
    )
    assert response.status_code == 401


def test_get_current_user_requires_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_get_current_user_with_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "me@example.com",
            "username": "meuser",
            "full_name": "Me User",
            "password": "StrongPassword123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "me@example.com", "password": "StrongPassword123!"},
    )
    token = login_response.get_json()["data"]["access_token"]
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == "me@example.com"


def test_refresh_token_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "username": "refreshuser",
            "full_name": "Refresh User",
            "password": "StrongPassword123!",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "StrongPassword123!"},
    )
    refresh_token = login_response.get_json()["data"]["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["access_token"]


def test_forgot_password_unknown_email_does_not_reveal_account(client):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "missing@example.com"},
    )
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_reset_password_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "reset@example.com",
            "username": "resetuser",
            "full_name": "Reset User",
            "password": "StrongPassword123!",
        },
    )
    forgot_response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "reset@example.com"},
    )
    payload = forgot_response.get_json()
    token = payload["meta"].get("reset_token")
    assert token is not None
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "NewStrongPassword123!"},
    )
    assert response.status_code == 200
