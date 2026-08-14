import pytest

from backend.app import create_app, db
from backend.app.services.support_services import NotificationService


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


def token_for(client, email, username):
    client.post("/api/v1/auth/register", json={"email": email, "username": username, "full_name": username, "password": "StrongPassword123!"})
    return client.post("/api/v1/auth/login", json={"email": email, "password": "StrongPassword123!"}).get_json()["data"]["access_token"]


def user_id(client, token):
    return client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}).get_json()["data"]["id"]


def create_org_project(client, token, slug):
    headers = {"Authorization": f"Bearer {token}"}
    org = client.post("/api/v1/organizations", json={"name": slug, "slug": slug}, headers=headers).get_json()["data"]["id"]
    project = client.post("/api/v1/projects", json={"organization_id": org, "name": "Project", "status": "Active", "priority": "Medium"}, headers=headers).get_json()["data"]["id"]
    return org, project


def test_notification_list_empty_unread_and_read_lifecycle(client, app):
    token = token_for(client, "notice@example.com", "notice")
    headers = {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/notifications", headers=headers).get_json()["data"] == []
    with app.app_context():
        notification = NotificationService().create(user_id(client, token), "TASK_ASSIGNED", "You were assigned a task", "Task A", "task", "00000000-0000-0000-0000-000000000001")
        db.session.commit()
        notification_id = str(notification.id)
    assert client.get("/api/v1/notifications/unread-count", headers=headers).get_json()["data"]["count"] == 1
    read = client.patch(f"/api/v1/notifications/{notification_id}/read", headers=headers)
    assert read.status_code == 200 and read.get_json()["data"]["is_read"] is True
    assert read.get_json()["data"]["read_at"]
    assert client.patch("/api/v1/notifications/read-all", headers=headers).status_code == 200


def test_notification_is_private_to_recipient(client, app):
    owner_token = token_for(client, "recipient@example.com", "recipient")
    outsider_token = token_for(client, "other@example.com", "other")
    with app.app_context():
        notification = NotificationService().create(user_id(client, owner_token), "TASK_ASSIGNED", "Private", "Only recipient", "task", "00000000-0000-0000-0000-000000000002")
        db.session.commit()
        notification_id = str(notification.id)
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}
    assert client.get("/api/v1/notifications", headers=outsider_headers).get_json()["data"] == []
    assert client.patch(f"/api/v1/notifications/{notification_id}/read", headers=outsider_headers).status_code == 404
    assert client.delete(f"/api/v1/notifications/{notification_id}", headers=outsider_headers).status_code == 404


def test_assignment_project_and_team_membership_notifications(client):
    owner_token = token_for(client, "owner-notify@example.com", "ownernotify")
    member_token = token_for(client, "member-notify@example.com", "membernotify")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    member_headers = {"Authorization": f"Bearer {member_token}"}
    member_id = user_id(client, member_token)
    org_id, project_id = create_org_project(client, owner_token, "notification-org")
    assert client.post(f"/api/v1/organizations/{org_id}/members", json={"user_id": member_id, "role": "Team Member"}, headers=owner_headers).status_code == 201
    assert client.post(f"/api/v1/projects/{project_id}/members", json={"user_id": member_id}, headers=owner_headers).status_code == 201
    team_id = client.post("/api/v1/teams", json={"organization_id": org_id, "name": "Notify Team"}, headers=owner_headers).get_json()["data"]["id"]
    assert client.post(f"/api/v1/teams/{team_id}/members", json={"user_id": member_id}, headers=owner_headers).status_code == 201
    task = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Assigned", "assignee_id": member_id}, headers=owner_headers)
    assert task.status_code == 201
    notifications = client.get("/api/v1/notifications?per_page=20", headers=member_headers).get_json()["data"]
    assert {item["event_type"] for item in notifications} == {"PROJECT_ADDED", "TEAM_ADDED", "TASK_ASSIGNED"}


def test_notification_endpoints_require_authentication(client):
    assert client.get("/api/v1/notifications").status_code == 401
    assert client.get("/api/v1/notifications/unread-count").status_code == 401
