# Teams API Specification

## Base URL

/api/v1/teams

## Endpoints

### Create Team

POST /api/v1/teams

#### Purpose
Create a new team within an organization.

#### Authentication
JWT required.

#### Permission
`team:create`

#### Request Body
```json
{
  "organization_id": "uuid",
  "name": "Engineering",
  "description": "Core engineering team",
  "lead_user_id": "uuid"
}
```

### List Teams

GET /api/v1/teams

#### Purpose
List teams visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`team:read`

### Get Team by ID

GET /api/v1/teams/{id}

#### Purpose
Retrieve team details.

#### Authentication
JWT required.

#### Permission
`team:read`

### Update Team

PATCH /api/v1/teams/{id}

#### Purpose
Update team metadata.

#### Authentication
JWT required.

#### Permission
`team:update`

### Delete Team

DELETE /api/v1/teams/{id}

#### Purpose
Delete or archive a team.

#### Authentication
JWT required.

#### Permission
`team:delete`

### List Team Members

GET /api/v1/teams/{id}/members

#### Purpose
List the members of a team.

#### Authentication
JWT required.

#### Permission
`team:read`

### Add Team Member

POST /api/v1/teams/{id}/members

#### Purpose
Add a user to a team.

#### Authentication
JWT required.

#### Permission
`team:member:create`

### Remove Team Member

DELETE /api/v1/teams/{id}/members/{userId}

#### Purpose
Remove a user from a team.

#### Authentication
JWT required.

#### Permission
`team:member:delete`
