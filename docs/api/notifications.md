# Notifications API Specification

## Base URL

/api/v1/notifications

## Endpoints

### List Notifications

GET /api/v1/notifications

#### Purpose
List notifications for the authenticated user.

#### Authentication
JWT required.

#### Permission
None.

#### Query Parameters
- `is_read`
- `page`
- `per_page`

### Get Notification by ID

GET /api/v1/notifications/{id}

#### Purpose
Retrieve a specific notification.

#### Authentication
JWT required.

#### Permission
None.

### Mark Notification as Read

PATCH /api/v1/notifications/{id}

#### Purpose
Mark a notification as read.

#### Authentication
JWT required.

#### Permission
None.

### Delete Notification

DELETE /api/v1/notifications/{id}

#### Purpose
Delete a notification.

#### Authentication
JWT required.

#### Permission
None.

### Mark All Notifications as Read

PATCH /api/v1/notifications/read-all

#### Purpose
Mark all visible notifications as read.

#### Authentication
JWT required.

#### Permission
None.

### Clear All Notifications

DELETE /api/v1/notifications/clear-all

#### Purpose
Delete all visible notifications for the user.

#### Authentication
JWT required.

#### Permission
None.
