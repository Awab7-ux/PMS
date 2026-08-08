# API Endpoints Specification

## 1. Authentication Endpoints

### Public authentication routes
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh
- POST /api/auth/forgot-password
- POST /api/auth/reset-password
- POST /api/auth/verify-email

### Authentication flow
1. Register a new user account.
2. Verify email address.
3. Login to receive access and refresh tokens.
4. Send the access token in the Authorization header for protected requests.
5. Refresh the access token when it expires.
6. Logout to invalidate the active session.

## 2. User Endpoints

- GET /api/users
- GET /api/users/{id}
- PATCH /api/users/{id}
- DELETE /api/users/{id}
- GET /api/users/me
- PATCH /api/users/me

## 3. Organization Endpoints

- POST /api/organizations
- GET /api/organizations
- GET /api/organizations/{id}
- PATCH /api/organizations/{id}
- DELETE /api/organizations/{id}
- GET /api/organizations/{id}/members
- POST /api/organizations/{id}/members
- PATCH /api/organizations/{id}/members/{userId}
- DELETE /api/organizations/{id}/members/{userId}

## 4. Team Endpoints

- POST /api/teams
- GET /api/teams
- GET /api/teams/{id}
- PATCH /api/teams/{id}
- DELETE /api/teams/{id}
- GET /api/teams/{id}/members
- POST /api/teams/{id}/members
- DELETE /api/teams/{id}/members/{userId}

## 5. Project Endpoints

- POST /api/projects
- GET /api/projects
- GET /api/projects/{id}
- PATCH /api/projects/{id}
- DELETE /api/projects/{id}
- GET /api/projects/{id}/members
- POST /api/projects/{id}/members
- PATCH /api/projects/{id}/members/{userId}
- DELETE /api/projects/{id}/members/{userId}

## 6. Task Endpoints

- POST /api/tasks
- GET /api/tasks
- GET /api/tasks/{id}
- PATCH /api/tasks/{id}
- DELETE /api/tasks/{id}
- POST /api/tasks/{id}/subtasks
- GET /api/tasks/{id}/subtasks
- PATCH /api/tasks/{id}/subtasks/{subtaskId}
- DELETE /api/tasks/{id}/subtasks/{subtaskId}

## 7. Comment Endpoints

- POST /api/comments
- GET /api/comments
- GET /api/comments/{id}
- PATCH /api/comments/{id}
- DELETE /api/comments/{id}
- GET /api/tasks/{id}/comments
- POST /api/tasks/{id}/comments

## 8. File Endpoints

- POST /api/files/upload
- GET /api/files
- GET /api/files/{id}
- PATCH /api/files/{id}
- DELETE /api/files/{id}
- GET /api/tasks/{id}/files
- POST /api/tasks/{id}/files

## 9. Notification Endpoints

- GET /api/notifications
- GET /api/notifications/{id}
- PATCH /api/notifications/{id}
- DELETE /api/notifications/{id}
- PATCH /api/notifications/read-all
- DELETE /api/notifications/clear-all

## 10. Calendar Endpoints

- POST /api/calendar
- GET /api/calendar
- GET /api/calendar/{id}
- PATCH /api/calendar/{id}
- DELETE /api/calendar/{id}
- GET /api/projects/{id}/calendar

## 11. Message Endpoints

- GET /api/messages/channels
- POST /api/messages/channels
- GET /api/messages/channels/{id}
- POST /api/messages/channels/{id}/messages
- GET /api/messages/channels/{id}/messages
- PATCH /api/messages/{id}
- DELETE /api/messages/{id}

## 12. Report Endpoints

- POST /api/reports
- GET /api/reports
- GET /api/reports/{id}
- DELETE /api/reports/{id}
- GET /api/projects/{id}/reports

## 13. Analytics Endpoints

- GET /api/analytics/dashboard
- GET /api/analytics/projects
- GET /api/analytics/tasks
- GET /api/analytics/users
- GET /api/analytics/organizations/{id}

## 14. Administration Endpoints

- GET /api/admin/roles
- POST /api/admin/roles
- PATCH /api/admin/roles/{id}
- DELETE /api/admin/roles/{id}
- GET /api/admin/permissions
- GET /api/admin/activity-logs
- GET /api/admin/settings
- PATCH /api/admin/settings
