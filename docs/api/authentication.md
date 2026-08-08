# Authentication API Specification

## Base URL

/api/v1/auth

## Endpoints

### Register User

POST /api/v1/auth/register

#### Purpose
Create a new user account for the PMS platform.

#### Authentication
No authentication required.

#### Permission
None.

#### Request Body
```json
{
  "email": "user@example.com",
  "username": "jdoe",
  "full_name": "Jane Doe",
  "password": "StrongPassword123!"
}
```

#### Validation Rules
- `email` must be a valid email address.
- `username` must be unique and between 3 and 50 characters.
- `full_name` must not be empty.
- `password` must meet minimum strength requirements.

#### Success Response
- `201 Created`

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "jdoe",
      "full_name": "Jane Doe",
      "is_active": false
    }
  },
  "message": "Registration successful. Please verify your email.",
  "meta": {}
}
```

#### Error Responses
- `400 Bad Request` for invalid payload
- `409 Conflict` for duplicate email or username

### Login

POST /api/v1/auth/login

#### Purpose
Authenticate a user and issue tokens.

#### Authentication
No authentication required.

#### Permission
None.

#### Request Body
```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

#### Validation Rules
- `email` and `password` are required.

#### Success Response
- `200 OK`

```json
{
  "success": true,
  "data": {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": "Login successful.",
  "meta": {}
}
```

#### Error Responses
- `401 Unauthorized` for invalid credentials
- `422 Unprocessable Entity` for missing fields

### Logout

POST /api/v1/auth/logout

#### Purpose
Invalidate the current authentication session.

#### Authentication
JWT required.

#### Permission
None.

#### Success Response
- `200 OK`

```json
{
  "success": true,
  "data": {},
  "message": "Logout successful.",
  "meta": {}
}
```

### Refresh Token

POST /api/v1/auth/refresh

#### Purpose
Issue a new access token using a refresh token.

#### Authentication
Refresh token required.

#### Permission
None.

#### Request Body
```json
{
  "refresh_token": "jwt_refresh_token"
}
```

#### Success Response
- `200 OK`

```json
{
  "success": true,
  "data": {
    "access_token": "new_jwt_access_token",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": null,
  "meta": {}
}
```

### Forgot Password

POST /api/v1/auth/forgot-password

#### Purpose
Initiate password recovery.

#### Authentication
No authentication required.

#### Permission
None.

#### Request Body
```json
{
  "email": "user@example.com"
}
```

#### Success Response
- `200 OK`

### Reset Password

POST /api/v1/auth/reset-password

#### Purpose
Set a new password using a recovery token.

#### Authentication
No authentication required.

#### Request Body
```json
{
  "token": "recovery_token",
  "new_password": "NewStrongPassword123!"
}
```

### Verify Email

POST /api/v1/auth/verify-email

#### Purpose
Verify the user’s email address.

#### Authentication
No authentication required.

#### Request Body
```json
{
  "token": "verification_token"
}
```
