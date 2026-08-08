# Tasks API Specification

## Base URL

/api/v1/tasks

## Endpoints

### Create Task

POST /api/v1/tasks

#### Purpose
Create a new task inside a project.

#### Authentication
JWT required.

#### Permission
`task:create`

#### Request Body
```json
{
  "project_id": "uuid",
  "title": "Implement login flow",
  "description": "Add authentication UI and backend validation",
  "status": "To Do",
  "priority": "High",
  "assignee_id": "uuid",
  "reporter_id": "uuid",
  "due_date": "2026-08-20"
}
```

#### Validation Rules
- `project_id` must reference an existing project.
- `title` is required.
- `status` must be one of the allowed task statuses.
- `priority` must be one of the allowed task priorities.

### List Tasks

GET /api/v1/tasks

#### Purpose
List tasks visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`task:read`

#### Query Parameters
- `project_id`
- `assignee_id`
- `status`
- `priority`
- `due_before`
- `due_after`
- `search`
- `page`
- `per_page`

### Get Task by ID

GET /api/v1/tasks/{id}

#### Purpose
Retrieve a specific task.

#### Authentication
JWT required.

#### Permission
`task:read`

### Update Task

PATCH /api/v1/tasks/{id}

#### Purpose
Update a task’s fields or status.

#### Authentication
JWT required.

#### Permission
`task:update`

### Delete Task

DELETE /api/v1/tasks/{id}

#### Purpose
Archive or delete a task.

#### Authentication
JWT required.

#### Permission
`task:delete`

### Create Subtask

POST /api/v1/tasks/{id}/subtasks

#### Purpose
Create a subtask under a task.

#### Authentication
JWT required.

#### Permission
`task:create`

### List Subtasks

GET /api/v1/tasks/{id}/subtasks

#### Purpose
List subtasks for a task.

#### Authentication
JWT required.

#### Permission
`task:read`

### Update Subtask

PATCH /api/v1/tasks/{id}/subtasks/{subtaskId}

#### Purpose
Update an existing subtask.

#### Authentication
JWT required.

#### Permission
`task:update`

### Delete Subtask

DELETE /api/v1/tasks/{id}/subtasks/{subtaskId}

#### Purpose
Delete a subtask.

#### Authentication
JWT required.

#### Permission
`task:delete`
