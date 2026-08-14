import pytest

from backend.app import create_app, db


@pytest.fixture()
def client():
    app = create_app("testing")
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all()
        db.create_all()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()


def register_and_login(client, email, username, full_name, password="StrongPassword123!"):
    client.post("/api/v1/auth/register", json={"email": email, "username": username, "full_name": full_name, "password": password})
    return client.post("/api/v1/auth/login", json={"email": email, "password": password}).get_json()["data"]["access_token"]


def create_org(client, token, name, slug):
    return client.post("/api/v1/organizations", json={"name": name, "slug": slug}, headers={"Authorization": f"Bearer {token}"}).get_json()["data"]["id"]


def create_project(client, token, org_id, name):
    return client.post("/api/v1/projects", json={"organization_id": org_id, "name": name, "status": "Active", "priority": "Medium"}, headers={"Authorization": f"Bearer {token}"}).get_json()["data"]["id"]


def setup_event(client):
    token = register_and_login(client, "events@example.com", "eventsuser", "Events User")
    org_id = create_org(client, token, "Events Org", "events-org")
    project_id = create_project(client, token, org_id, "Events Project")
    return {"Authorization": f"Bearer {token}"}, org_id, project_id


def test_event_crud_and_combined_calendar_feed(client):
    headers, org_id, project_id = setup_event(client)
    created = client.post("/api/v1/events", json={"organization_id": org_id, "project_id": project_id, "title": "Planning", "start_at": "2030-01-10T10:00:00Z", "end_at": "2030-01-10T11:00:00Z"}, headers=headers)
    assert created.status_code == 201
    event_id = created.get_json()["data"]["id"]
    assert client.get(f"/api/v1/events/{event_id}", headers=headers).status_code == 200
    updated = client.patch(f"/api/v1/events/{event_id}", json={"title": "Updated planning", "start_at": "2030-01-11T10:00:00Z", "end_at": "2030-01-11T11:00:00Z"}, headers=headers)
    assert updated.status_code == 200
    assert updated.get_json()["data"]["title"] == "Updated planning"
    task = client.post("/api/v1/tasks", json={"project_id": project_id, "title": "Due task", "due_date": "2030-01-11"}, headers=headers)
    assert task.status_code == 201
    feed = client.get(f"/api/v1/calendar/events?organization_id={org_id}&start=2030-01-01&end=2030-01-31", headers=headers)
    assert feed.status_code == 200
    assert {item["type"] for item in feed.get_json()["data"]["events"]} == {"task", "event"}
    assert client.delete(f"/api/v1/events/{event_id}", headers=headers).status_code == 200


def test_event_validation_range_filter_and_organization_isolation(client):
    headers, org_id, project_id = setup_event(client)
    invalid = client.post("/api/v1/events", json={"organization_id": org_id, "project_id": project_id, "title": "Bad", "start_at": "2030-01-10T11:00:00Z", "end_at": "2030-01-10T10:00:00Z"}, headers=headers)
    assert invalid.status_code == 400
    all_day = client.post("/api/v1/events", json={"organization_id": org_id, "title": "Away", "all_day": True, "start_at": "2030-02-10T00:00:00Z"}, headers=headers)
    assert all_day.status_code == 201
    listed = client.get(f"/api/v1/events?organization_id={org_id}&start=2030-02-01&end=2030-02-28", headers=headers)
    assert [item["title"] for item in listed.get_json()["data"]["items"]] == ["Away"]
    outsider_token = register_and_login(client, "eventoutsider@example.com", "eventoutsider", "Event Outsider")
    outsider = {"Authorization": f"Bearer {outsider_token}"}
    event_id = all_day.get_json()["data"]["id"]
    assert client.get(f"/api/v1/events/{event_id}", headers=outsider).status_code == 403
    assert client.patch(f"/api/v1/events/{event_id}", json={"title": "Nope"}, headers=outsider).status_code == 403
    assert client.delete(f"/api/v1/events/{event_id}", headers=outsider).status_code == 403
