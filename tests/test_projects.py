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


def create_org(client, token, name="Acme", slug="acme"):
    response = client.post(
        "/api/v1/organizations",
        json={"name": name, "slug": slug, "description": "Test org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.get_json()["data"]["id"]


def test_create_project_requires_auth(client):
    response = client.post(
        "/api/v1/projects",
        json={"organization_id": "00000000-0000-0000-0000-000000000001", "name": "Test"},
    )
    assert response.status_code == 401


def test_create_and_list_projects(client):
    token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, token)

    response = client.post(
        "/api/v1/projects",
        json={
            "organization_id": org_id,
            "name": "Website Redesign",
            "code": "WEB-001",
            "description": "Redesign project",
            "status": "Planning",
            "priority": "High",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "Website Redesign"
    assert payload["data"]["status"] == "Planning"

    list_response = client.get(
        f"/api/v1/projects?organization_id={org_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    data = list_response.get_json()
    assert len(data["data"]) == 1
    assert data["meta"]["pagination"]["total"] == 1


def test_get_and_update_project(client):
    token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, token)

    create_response = client.post(
        "/api/v1/projects",
        json={"organization_id": org_id, "name": "Alpha Project", "code": "ALPHA"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create_response.get_json()["data"]["id"]

    get_response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"status": "Active", "progress_percent": 25},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["data"]["status"] == "Active"
    assert update_response.get_json()["data"]["progress_percent"] == 25


def test_project_member_cannot_access_without_membership(client):
    owner_token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, owner_token)

    create_response = client.post(
        "/api/v1/projects",
        json={"organization_id": org_id, "name": "Private Project"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    project_id = create_response.get_json()["data"]["id"]

    other_token = register_and_login(client, "other@example.com", "other", "Other User")
    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": "other@example.com", "role": "team_member"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 403


def test_add_project_member(client):
    owner_token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, owner_token)

    create_response = client.post(
        "/api/v1/projects",
        json={"organization_id": org_id, "name": "Team Project"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    project_id = create_response.get_json()["data"]["id"]

    member_token = register_and_login(client, "member@example.com", "member", "Team Member")
    client.post(
        f"/api/v1/organizations/{org_id}/members",
        json={"user_id": "member@example.com", "role": "team_member"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    add_response = client.post(
        f"/api/v1/projects/{project_id}/members",
        json={"user_id": "member@example.com", "access_level": "member"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert add_response.status_code == 201

    access_response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert access_response.status_code == 200


def test_delete_project(client):
    token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, token)

    create_response = client.post(
        "/api/v1/projects",
        json={"organization_id": org_id, "name": "To Archive"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create_response.get_json()["data"]["id"]

    delete_response = client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 200

    get_response = client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404
