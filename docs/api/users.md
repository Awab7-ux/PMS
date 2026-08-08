# Users API Specification

## Base URL

/api/v1/users

## Endpoints

### List Users

GET /api/v1/users

#### Purpose
List users visible to the authenticated user.

#### Authentication
JWT required.

#### Permission
`user:read` or organization administrator access.

#### Query Parameters
- `page`
- `per_page`
- `search`
- `organization_id`
- `is_active`

#### Success Response
- `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "username": "jdoe",
      "full_name": "Jane Doe",
      "is_active": true
    }
  ],
  "message": null,
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

### Get Current User

GET /api/v1/users/me

#### Purpose
Retrieve the authenticated user profile.

#### Authentication
JWT required.

#### Permission
None.

#### Success Response
- `200 OK`

### Get User by ID

GET /api/v1/users/{id}

#### Purpose
Retrieve a specific user profile.

#### Authentication
JWT required.

#### Permission
`user:read` or self access.

#### Path Parameters
- `id`: user UUID

### Update Current User

PATCH /api/v1/users/me

#### Purpose
Update the authenticated user profile.

#### Authentication
JWT required.

#### Permission
None.

#### Request Body
```json
{
  "full_name": "Jane Smith",
  "avatar_url": "https://example.com/avatar.png"
}
```

### Update User by ID

PATCH /api/v1/users/{id}

#### Purpose
Update another user profile when authorized.

#### Authentication
JWT required.

#### Permission
`user:update`

### Delete User by ID

DELETE /api/v1/users/{id}

#### Purpose
Deactivate or remove a user account.

#### Authentication
JWT required.

#### Permission
`user:delete`

#### Success Response
- `204 No Content`
