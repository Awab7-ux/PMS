# Organizations API Specification

## Base URL

/api/v1/organizations

## Endpoints

### Create Organization

POST /api/v1/organizations

#### Purpose
Create a new organization workspace.

#### Authentication
JWT required.

#### Permission
`organization:create`

#### Request Body
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "description": "Operations workspace",
  "industry": "Technology"
}
```

#### Validation Rules
- `name` is required.
- `slug` must be unique and URL-safe.

#### Success Response
- `201 Created`

### List Organizations

GET /api/v1/organizations

#### Purpose
List organizations accessible to the user.

#### Authentication
JWT required.

#### Permission
`organization:read`

### Get Organization by ID

GET /api/v1/organizations/{id}

#### Purpose
Retrieve organization details.

#### Authentication
JWT required.

#### Permission
`organization:read`

### Update Organization

PATCH /api/v1/organizations/{id}

#### Purpose
Update organization settings.

#### Authentication
JWT required.

#### Permission
`organization:update`

### Delete Organization

DELETE /api/v1/organizations/{id}

#### Purpose
Archive or delete an organization.

#### Authentication
JWT required.

#### Permission
`organization:delete`

### List Organization Members

GET /api/v1/organizations/{id}/members

#### Purpose
List members in an organization.

#### Authentication
JWT required.

#### Permission
`organization:member:read`

### Add Organization Member

POST /api/v1/organizations/{id}/members

#### Purpose
Invite or add a member to an organization.

#### Authentication
JWT required.

#### Permission
`organization:member:create`

### Update Organization Member

PATCH /api/v1/organizations/{id}/members/{userId}

#### Purpose
Update a member’s role or status.

#### Authentication
JWT required.

#### Permission
`organization:member:update`

### Remove Organization Member

DELETE /api/v1/organizations/{id}/members/{userId}

#### Purpose
Remove a member from an organization.

#### Authentication
JWT required.

#### Permission
`organization:member:delete`
