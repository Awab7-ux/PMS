# Reports API Specification

## Base URL

/api/v1/reports

## Endpoints

### Create Report

POST /api/v1/reports

#### Purpose
Generate or store a new report entry.

#### Authentication
JWT required.

#### Permission
`report:create`

#### Request Body
```json
{
  "organization_id": "uuid",
  "project_id": "uuid",
  "report_type": "project_progress",
  "title": "Weekly Summary"
}
```

### List Reports

GET /api/v1/reports

#### Purpose
List reports visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`report:read`

### Get Report by ID

GET /api/v1/reports/{id}

#### Purpose
Retrieve a specific report.

#### Authentication
JWT required.

#### Permission
`report:read`

### Delete Report

DELETE /api/v1/reports/{id}

#### Purpose
Delete a report.

#### Authentication
JWT required.

#### Permission
`report:delete`

### List Project Reports

GET /api/v1/projects/{projectId}/reports

#### Purpose
List reports associated with a project.

#### Authentication
JWT required.

#### Permission
`report:read`
