# Files API Specification

## Base URL

/api/v1/files

## Endpoints

### Upload File

POST /api/v1/files/upload

#### Purpose
Upload a file attachment for a task or project context.

#### Authentication
JWT required.

#### Permission
`file:create`

#### Request Body
- multipart/form-data
- `file`
- `task_id` (optional)
- `project_id` (optional)
- `description` (optional)

#### Validation Rules
- File size must be within configured limits.
- Allowed file types must be validated.

### List Files

GET /api/v1/files

#### Purpose
List files visible to the requester.

#### Authentication
JWT required.

#### Permission
`file:read`

### Get File Metadata

GET /api/v1/files/{id}

#### Purpose
Retrieve metadata for a file.

#### Authentication
JWT required.

#### Permission
`file:read`

### Update File Metadata

PATCH /api/v1/files/{id}

#### Purpose
Update attachment metadata.

#### Authentication
JWT required.

#### Permission
`file:update`

### Delete File

DELETE /api/v1/files/{id}

#### Purpose
Delete a file attachment.

#### Authentication
JWT required.

#### Permission
`file:delete`

### List Task Files

GET /api/v1/tasks/{taskId}/files

#### Purpose
List files attached to a task.

#### Authentication
JWT required.

#### Permission
`file:read`
