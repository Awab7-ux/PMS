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


def register_and_login(client, email, username, full_name, password="StrongPassword123!"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "full_name": full_name,
            "password": password,
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login_response.get_json()["data"]["access_token"]


def test_create_organization_requires_auth(client):
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme", "slug": "acme", "description": "Ops"},
    )
    assert response.status_code == 401


def test_create_and_get_organization(client):
    token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme", "slug": "acme", "description": "Ops"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "Acme"

    get_response = client.get(
        "/api/v1/organizations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert len(get_response.get_json()["data"]) == 1


def test_cannot_access_other_organization(client):
    owner_token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    client.post(
        "/api/v1/organizations",
        json={"name": "Acme", "slug": "acme", "description": "Ops"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    other_token = register_and_login(client, "user@example.com", "user", "User One")
    response = client.get(
        "/api/v1/organizations/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404


def test_organization_member_management_and_role_escalation_prevention(client):
    owner_token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme", "slug": "acme", "description": "Ops"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_response.get_json()["data"]["id"]

    member_token = register_and_login(client, "member@example.com", "member", "Team Member")
    add_response = client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": "member@example.com", "role": "team_member"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_response.status_code == 201

    escalation_response = client.patch(
        f"/api/v1/organizations/{org_id}/members/{org_id}",
        json={"role": "organization_owner"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert escalation_response.status_code == 400


def test_create_team_and_add_member(client):
    owner_token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_response = client.post(
        "/api/v1/organizations",
        json={"name": "Acme", "slug": "acme", "description": "Ops"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    org_id = org_response.get_json()["data"]["id"]

    team_response = client.post(
        "/api/v1/teams",
        json={"organization_id": org_id, "name": "Engineering", "description": "Core team"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert team_response.status_code == 201
    team_id = team_response.get_json()["data"]["id"]

    member_token = register_and_login(client, "member@example.com", "member", "Team Member")
    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": "member@example.com", "role": "team_member"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    add_team_member_response = client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"user_id": "member@example.com"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_team_member_response.status_code == 201


def test_cross_organization_team_access_prevention(client):
    owner_a_token = register_and_login(client, "ownera@example.com", "ownera", "Owner A")
    org_a_response = client.post(
        "/api/v1/organizations",
        json={"name": "Org A", "slug": "org-a", "description": "A"},
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    org_a_id = org_a_response.get_json()["data"]["id"]

    team_response = client.post(
        "/api/v1/teams",
        json={"organization_id": org_a_id, "name": "Alpha", "description": "A team"},
        headers={"Authorization": f"Bearer {owner_a_token}"},
    )
    team_id = team_response.get_json()["data"]["id"]

    owner_b_token = register_and_login(client, "ownerb@example.com", "ownerb", "Owner B")
    client.post(
        "/api/v1/organizations",
        json={"name": "Org B", "slug": "org-b", "description": "B"},
        headers={"Authorization": f"Bearer {owner_b_token}"},
    )

    response = client.get(
        f"/api/v1/teams/{team_id}",
        headers={"Authorization": f"Bearer {owner_b_token}"},
    )
    assert response.status_code == 403
