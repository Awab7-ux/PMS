# Calendar API Specification

## Base URL

/api/v1/calendar

## Endpoints

### Create Calendar Event

POST /api/v1/calendar

#### Purpose
Create a calendar event for an organization or project.

#### Authentication
JWT required.

#### Permission
`calendar:create`

#### Request Body
```json
{
  "organization_id": "uuid",
  "project_id": "uuid",
  "title": "Sprint Planning",
  "description": "Team planning session",
  "event_type": "meeting",
  "start_at": "2026-08-10T09:00:00Z",
  "end_at": "2026-08-10T10:00:00Z",
  "location": "Teams"
}
```

### List Calendar Events

GET /api/v1/calendar

#### Purpose
List calendar events visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`calendar:read`

#### Query Parameters
- `start_date`
- `end_date`
- `project_id`
- `organization_id`

### Get Calendar Event by ID

GET /api/v1/calendar/{id}

#### Purpose
Retrieve a single calendar event.

#### Authentication
JWT required.

#### Permission
`calendar:read`

### Update Calendar Event

PATCH /api/v1/calendar/{id}

#### Purpose
Update a calendar event.

#### Authentication
JWT required.

#### Permission
`calendar:update`

### Delete Calendar Event

DELETE /api/v1/calendar/{id}

#### Purpose
Delete a calendar event.

#### Authentication
JWT required.

#### Permission
`calendar:delete`

### List Project Calendar Events

GET /api/v1/projects/{projectId}/calendar

#### Purpose
List calendar events for a specific project.

#### Authentication
JWT required.

#### Permission
`calendar:read`
