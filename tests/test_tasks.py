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
