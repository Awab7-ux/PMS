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
        json={"email": email, "username": username, "full_name": full_name, "password": password},
    )
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_response.get_json()["data"]["access_token"]


def create_org(client, token, name="Acme", slug="acme"):
    response = client.post(
        "/api/v1/organizations",
        json={"name": name, "slug": slug, "description": "Test org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.get_json()["data"]["id"]


def create_project(client, token, org_id, name="Test Project"):
    response = client.post(
        "/api/v1/projects",
        json={"organization_id": org_id, "name": name, "status": "Active", "priority": "Medium"},
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.get_json()["data"]["id"]


def test_create_task(client):
    token = register_and_login(client, "owner@example.com", "owner", "Org Owner")
    org_id = create_org(client, token)
    project_id = create_project(client, token, org_id)

    response = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Build API", "status": "TODO", "priority": "HIGH"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.get_json()["data"]
    assert data["title"] == "Build API"
    assert data["status"] == "TODO"
    assert data["priority"] == "HIGH"


def test_list_and_get_task(client):
    token = register_and_login(client, "user@example.com", "user1", "User One")
    org_id = create_org(client, token)
    project_id = create_project(client, token, org_id)

    create_resp = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Task A"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = create_resp.get_json()["data"]["id"]

    list_resp = client.get(
        f"/api/v1/tasks?project_id={project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["data"]) == 1

    get_resp = client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 200
    assert get_resp.get_json()["data"]["title"] == "Task A"


def test_subtasks_and_progress(client):
    token = register_and_login(client, "sub@example.com", "subuser", "Sub User")
    org_id = create_org(client, token)
    project_id = create_project(client, token, org_id)

    task_resp = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Parent Task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = task_resp.get_json()["data"]["id"]

    sub1 = client.post(
        f"/api/v1/tasks/{task_id}/subtasks",
        json={"title": "Sub 1"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sub1.status_code == 201
    sub1_id = sub1.get_json()["data"]["id"]

    client.post(
        f"/api/v1/tasks/{task_id}/subtasks",
        json={"title": "Sub 2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    client.patch(
        f"/api/v1/tasks/{task_id}/subtasks/{sub1_id}",
        json={"is_completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    get_resp = client.get(f"/api/v1/tasks/{task_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.get_json()["data"]["progress_percent"] == 50


def test_kanban_board_and_move(client):
    token = register_and_login(client, "kanban@example.com", "kanbanuser", "Kanban User")
    org_id = create_org(client, token)
    project_id = create_project(client, token, org_id)

    task_resp = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Move Me", "status": "TODO"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = task_resp.get_json()["data"]["id"]

    board_resp = client.get(
        f"/api/v1/tasks/kanban/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert board_resp.status_code == 200
    board = board_resp.get_json()["data"]
    assert "TODO" in board

    move_resp = client.post(
        f"/api/v1/tasks/{task_id}/move",
        json={"status": "IN_PROGRESS", "kanban_order": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert move_resp.status_code == 200
    assert move_resp.get_json()["data"]["status"] == "IN_PROGRESS"


def test_task_rejects_assignee_outside_organization(client):
    owner_token = register_and_login(client, "isolation-owner@example.com", "isoowner", "Isolation Owner")
    org_id = create_org(client, owner_token, "Isolation Org", "isolation-org")
    project_id = create_project(client, owner_token, org_id, "Isolation Project")
    outsider_token = register_and_login(client, "outsider@example.com", "outsider", "Outside User")

    outsider_me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {outsider_token}"})
    outsider_id = outsider_me.get_json()["data"]["id"]
    response = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Private task", "assignee_id": outsider_id},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 403


def test_comments(client):
    token = register_and_login(client, "comment@example.com", "commentuser", "Comment User")
    org_id = create_org(client, token)
    project_id = create_project(client, token, org_id)

    task_resp = client.post(
        "/api/v1/tasks",
        json={"project_id": project_id, "title": "Comment Task"},
        headers={"Authorization": f"Bearer {token}"},
    )
    task_id = task_resp.get_json()["data"]["id"]

    comment_resp = client.post(
        f"/api/v1/tasks/{task_id}/comments",
        json={"content": "Hello @commentuser"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert comment_resp.status_code == 201

    list_resp = client.get(
        f"/api/v1/tasks/{task_id}/comments",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["data"]) == 1


def test_update_status_priority_and_due_date_filter(client):
    token = register_and_login(client, "update@example.com", "updateuser", "Update User")
    org_id = create_org(client, token, "Update Org", "update-org")
    project_id = create_project(client, token, org_id, "Update Project")
    headers = {"Authorization": f"Bearer {token}"}
    task_id = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Before"}, headers=headers).get_json()["data"]["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "After", "status": "REVIEW", "priority": "HIGH", "due_date": "2030-01-15"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["status"] == "REVIEW"
    assert response.get_json()["data"]["priority"] == "HIGH"

    filtered = client.get(f"/api/v1/tasks?project_id={project_id}&due_date=2030-01-15", headers=headers)
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.get_json()["data"]] == [task_id]


def test_priority_validation_and_missing_task(client):
    token = register_and_login(client, "validation@example.com", "validationuser", "Validation User")
    org_id = create_org(client, token, "Validation Org", "validation-org")
    project_id = create_project(client, token, org_id, "Validation Project")
    headers = {"Authorization": f"Bearer {token}"}

    invalid = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Bad", "priority": "ASAP"}, headers=headers)
    assert invalid.status_code == 400
    missing = client.get("/api/v1/tasks/not-a-task-id", headers=headers)
    assert missing.status_code == 404


def test_delete_task_removes_it_from_task_list(client):
    token = register_and_login(client, "delete@example.com", "deleteuser", "Delete User")
    org_id = create_org(client, token, "Delete Org", "delete-org")
    project_id = create_project(client, token, org_id, "Delete Project")
    headers = {"Authorization": f"Bearer {token}"}
    task_id = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Remove me"}, headers=headers).get_json()["data"]["id"]

    assert client.delete(f"/api/v1/tasks/{task_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/tasks/{task_id}", headers=headers).status_code == 404
    assert client.get(f"/api/v1/tasks?project_id={project_id}", headers=headers).get_json()["data"] == []


def test_task_access_is_isolated_between_organizations(client):
    owner_token = register_and_login(client, "private-owner@example.com", "privateowner", "Private Owner")
    org_id = create_org(client, owner_token, "Private Org", "private-org")
    project_id = create_project(client, owner_token, org_id, "Private Project")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    task_id = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Private"}, headers=owner_headers).get_json()["data"]["id"]
    outsider_token = register_and_login(client, "private-outsider@example.com", "privateoutsider", "Private Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    assert client.get(f"/api/v1/tasks/{task_id}", headers=outsider_headers).status_code == 403
    assert client.patch(f"/api/v1/tasks/{task_id}", json={"status": "DONE"}, headers=outsider_headers).status_code == 403
    assert client.delete(f"/api/v1/tasks/{task_id}", headers=outsider_headers).status_code == 403


def test_task_accepts_assignee_in_same_organization(client):
    owner_token = register_and_login(client, "assign-owner@example.com", "assignowner", "Assign Owner")
    org_id = create_org(client, owner_token, "Assign Org", "assign-org")
    project_id = create_project(client, owner_token, org_id, "Assign Project")
    member_token = register_and_login(client, "assign-member@example.com", "assignmember", "Assign Member")
    member_id = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {member_token}"}).get_json()["data"]["id"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    add_member = client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": member_id, "role": "Team Member"}, headers=owner_headers)
    assert add_member.status_code == 201

    response = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Assigned", "assignee_id": member_id}, headers=owner_headers)
    assert response.status_code == 201
    assert response.get_json()["data"]["assignee_id"] == member_id
