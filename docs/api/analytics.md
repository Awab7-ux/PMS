# Analytics API Specification

## Base URL

/api/v1/analytics

## Endpoints

### Dashboard Metrics

GET /api/v1/analytics/dashboard

#### Purpose
Return organizational dashboard metrics.

#### Authentication
JWT required.

#### Permission
`analytics:read`

#### Query Parameters
- `organization_id`
- `project_id`
- `date_from`
- `date_to`

### Project Analytics

GET /api/v1/analytics/projects

#### Purpose
Return analytics aggregated by project.

#### Authentication
JWT required.

#### Permission
`analytics:read`

### Task Analytics

GET /api/v1/analytics/tasks

#### Purpose
Return analytics for task progress and workload.

#### Authentication
JWT required.

#### Permission
`analytics:read`

### User Analytics

GET /api/v1/analytics/users

#### Purpose
Return analytics related to user activity and workload.

#### Authentication
JWT required.

#### Permission
`analytics:read`

### Organization Analytics

GET /api/v1/analytics/organizations/{id}

#### Purpose
Return analytics for a specific organization.

#### Authentication
JWT required.

#### Permission
`analytics:read`
