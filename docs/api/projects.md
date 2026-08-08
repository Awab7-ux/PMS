# Projects API Specification

## Base URL

/api/v1/projects

## Endpoints

### Create Project

POST /api/v1/projects

#### Purpose
Create a new project under an organization.

#### Authentication
JWT required.

#### Permission
`project:create`

#### Request Body
```json
{
  "organization_id": "uuid",
  "name": "Website Redesign",
  "code": "WEB-001",
  "description": "Redesign project",
  "status": "Planning",
  "start_date": "2026-08-10",
  "end_date": "2026-09-10"
}
```

#### Validation Rules
- `name` is required.
- `organization_id` must reference an existing organization.
- `status` must be one of the allowed project statuses.

### List Projects

GET /api/v1/projects

#### Purpose
List projects visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`project:read`

#### Query Parameters
- `organization_id`
- `status`
- `search`
- `page`
- `per_page`

### Get Project by ID

GET /api/v1/projects/{id}

#### Purpose
Retrieve project details.

#### Authentication
JWT required.

#### Permission
`project:read`

### Update Project

PATCH /api/v1/projects/{id}

#### Purpose
Update an existing project.

#### Authentication
JWT required.

#### Permission
`project:update`

### Delete Project

DELETE /api/v1/projects/{id}

#### Purpose
Archive or delete a project.

#### Authentication
JWT required.

#### Permission
`project:delete`

### List Project Members

GET /api/v1/projects/{id}/members

#### Purpose
List project membership details.

#### Authentication
JWT required.

#### Permission
`project:member:read`

### Add Project Member

POST /api/v1/projects/{id}/members

#### Purpose
Add a user to the project.

#### Authentication
JWT required.

#### Permission
`project:member:create`

### Remove Project Member

DELETE /api/v1/projects/{id}/members/{userId}

#### Purpose
Remove a user from a project.

#### Authentication
JWT required.

#### Permission
`project:member:delete`
