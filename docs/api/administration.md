# Administration API Specification

## Base URL

/api/v1/admin

## Endpoints

### List Roles

GET /api/v1/admin/roles

#### Purpose
List organization or system roles.

#### Authentication
JWT required.

#### Permission
`admin:roles:read`

### Create Role

POST /api/v1/admin/roles

#### Purpose
Create a new role definition.

#### Authentication
JWT required.

#### Permission
`admin:roles:create`

### Update Role

PATCH /api/v1/admin/roles/{id}

#### Purpose
Update a role definition.

#### Authentication
JWT required.

#### Permission
`admin:roles:update`

### Delete Role

DELETE /api/v1/admin/roles/{id}

#### Purpose
Remove a role definition.

#### Authentication
JWT required.

#### Permission
`admin:roles:delete`

### List Permissions

GET /api/v1/admin/permissions

#### Purpose
List available permissions.

#### Authentication
JWT required.

#### Permission
`admin:permissions:read`

### List Activity Logs

GET /api/v1/admin/activity-logs

#### Purpose
Review system or organization activity.

#### Authentication
JWT required.

#### Permission
`admin:activity:read`

### Get Settings

GET /api/v1/admin/settings

#### Purpose
Retrieve admin settings.

#### Authentication
JWT required.

#### Permission
`admin:settings:read`

### Update Settings

PATCH /api/v1/admin/settings

#### Purpose
Update admin settings.

#### Authentication
JWT required.

#### Permission
`admin:settings:update`
