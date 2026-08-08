# Comments API Specification

## Base URL

/api/v1/comments

## Endpoints

### Create Comment

POST /api/v1/comments

#### Purpose
Create a comment for a task.

#### Authentication
JWT required.

#### Permission
`comment:create`

#### Request Body
```json
{
  "task_id": "uuid",
  "body": "This looks good."
}
```

### List Comments

GET /api/v1/comments

#### Purpose
List comments visible to the requester.

#### Authentication
JWT required.

#### Permission
`comment:read`

### Get Comment by ID

GET /api/v1/comments/{id}

#### Purpose
Retrieve a comment.

#### Authentication
JWT required.

#### Permission
`comment:read`

### Update Comment

PATCH /api/v1/comments/{id}

#### Purpose
Edit an existing comment.

#### Authentication
JWT required.

#### Permission
`comment:update`

### Delete Comment

DELETE /api/v1/comments/{id}

#### Purpose
Delete a comment.

#### Authentication
JWT required.

#### Permission
`comment:delete`

### List Task Comments

GET /api/v1/tasks/{taskId}/comments

#### Purpose
List comments associated with a task.

#### Authentication
JWT required.

#### Permission
`comment:read`

### Create Task Comment

POST /api/v1/tasks/{taskId}/comments

#### Purpose
Create a comment under a task.

#### Authentication
JWT required.

#### Permission
`comment:create`
