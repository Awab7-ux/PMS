# API Conventions

## 1. JSON Format

All API requests and responses should use JSON.

### Standard success response

```json
{
  "success": true,
  "data": {},
  "message": null,
  "meta": {}
}
```

### Standard error response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "The request contains invalid input.",
    "details": []
  },
  "meta": {}
}
```

## 2. Request Structure

Requests should include:
- JSON body for create and update operations
- Authorization header for protected routes
- Content-Type: application/json

## 3. Response Structure

### Success response fields
- `success`: boolean
- `data`: object or array containing the requested resource
- `message`: optional human-readable message
- `meta`: pagination, filters, and request metadata

### Error response fields
- `success`: false
- `error.code`: stable machine-readable error code
- `error.message`: summary of the failure
- `error.details`: array of field-specific validation issues
- `meta`: optional additional context

## 4. HTTP Status Codes

Recommended status codes:
- 200 OK for successful GET/PATCH operations
- 201 Created for successful POST operations
- 204 No Content for successful delete operations without a body
- 400 Bad Request for malformed input
- 401 Unauthorized for missing or invalid authentication
- 403 Forbidden for insufficient permissions
- 404 Not Found for missing resources
- 409 Conflict for duplicate or conflicting state
- 422 Unprocessable Entity for validation failures
- 500 Internal Server Error for unexpected failures

## 5. Pagination

Pagination should be supported on list endpoints.

Example query parameters:
- `page=1`
- `per_page=20`

Response metadata example:

```json
{
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 120,
    "pages": 6
  }
}
```

## 6. Filtering

List endpoints should support filters such as:
- `status`
- `project_id`
- `assignee_id`
- `organization_id`
- `is_read`
- `created_after`
- `created_before`

## 7. Sorting

Sorting should be supported via:
- `sort=created_at`
- `order=asc|desc`

## 8. Searching

Search should support simple keyword search and full-text-like behavior where relevant.

Example:
- `search=project alpha`

## 9. Validation Errors

Validation errors should be returned with field-level detail.

Example:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed.",
    "details": [
      {
        "field": "email",
        "message": "Email is required."
      }
    ]
  }
}
```

## 10. Authentication Errors

Authentication errors should return:
- 401 Unauthorized
- error code `AUTHENTICATION_REQUIRED` or `INVALID_TOKEN`

## 11. Authorization Errors

Authorization errors should return:
- 403 Forbidden
- error code `AUTHORIZATION_DENIED`

## 12. Resource-Not-Found Errors

Missing resources should return:
- 404 Not Found
- error code `RESOURCE_NOT_FOUND`
