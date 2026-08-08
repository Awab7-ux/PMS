# Backend Architecture Plan for PMS

## 1. Backend Goals

The backend for PMS will be implemented as a modular Flask application that follows a clear separation of concerns and remains consistent with the existing database schema, RBAC model, security architecture, and API specifications.

The architecture should support:
- multi-tenant organization isolation
- RESTful API endpoints under /api/v1/
- JWT-based authentication
- role-based authorization
- real-time collaboration through Flask-SocketIO
- asynchronous background tasks through Celery and Redis
- audit logging and notification workflows

## 2. Proposed Project Structure

A monolithic-first Flask application is the recommended starting point. The structure should remain organized so it can evolve into a more distributed system later if needed.

```text
backend/
├── app/
│   ├── __init__.py
│   ├── config/
│   ├── extensions/
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   ├── api/
│   │   ├── auth/
│   │   ├── users/
│   │   ├── organizations/
│   │   ├── teams/
│   │   ├── projects/
│   │   ├── tasks/
│   │   ├── comments/
│   │   ├── files/
│   │   ├── notifications/
│   │   ├── calendar/
│   │   ├── messaging/
│   │   ├── reports/
│   │   ├── analytics/
│   │   └── admin/
│   ├── websocket/
│   ├── tasks/
│   ├── utils/
│   └── errors/
├── tests/
├── migrations/
├── scripts/
├── requirements/
└── run.py
```

## 3. Directory Responsibilities

### app/__init__.py
Responsible for creating the Flask application instance using the application factory pattern.

### app/config
Contains environment-specific configuration for:
- Flask settings
- SQLAlchemy settings
- JWT settings
- Redis and Celery settings
- file storage settings
- logging settings

### app/extensions
Contains initialized Flask extensions such as:
- SQLAlchemy
- JWT manager
- SocketIO
- Celery
- Redis client helpers

### app/models
Contains SQLAlchemy ORM models for the database schema.

### app/schemas
Contains request and response serialization structures.

### app/repositories
Contains data-access abstractions for database queries and persistence.

### app/services
Contains business logic such as authentication, project management, task lifecycle handling, notifications, reporting, and analytics.

### app/api
Contains Flask blueprints grouped by domain.

### app/websocket
Contains WebSocket event handlers for real-time notifications, messaging, and task updates.

### app/tasks
Contains Celery task definitions for asynchronous workflows.

### app/utils
Contains cross-cutting utilities such as hashing, token helpers, date parsing, pagination, and common formatting helpers.

### app/errors
Contains centralized exception and error-response handling.

## 4. Application Factory Pattern

The backend should use a Flask application factory, typically exposed as `create_app()`.

### create_app() responsibilities
- Load configuration from environment variables or config classes
- Initialize Flask extensions
- Initialize the database engine and session management
- Initialize JWT support
- Initialize Redis and Celery clients
- Register blueprints for each API domain
- Register error handlers
- Initialize WebSocket support

### Proposed flow
1. Create Flask application instance
2. Load configuration
3. Initialize extension objects
4. Register application-level hooks
5. Register blueprints
6. Return application instance

## 5. Blueprint Architecture

Each domain should be implemented as a separate Flask blueprint.

### auth blueprint
Responsibilities:
- registration
- login
- logout
- token refresh
- password recovery
- email verification

### users blueprint
Responsibilities:
- current user profile operations
- user listing and lookup
- user profile updates

### organizations blueprint
Responsibilities:
- organization creation and updates
- member management
- tenant-level settings

### teams blueprint
Responsibilities:
- team creation and management
- team membership operations

### projects blueprint
Responsibilities:
- project CRUD operations
- membership management
- project-level analytics linkage

### tasks blueprint
Responsibilities:
- task creation and updates
- subtask operations
- status and priority workflows

### comments blueprint
Responsibilities:
- comment creation and management
- task-related discussion support

### files blueprint
Responsibilities:
- file upload metadata handling
- attachment listing and retrieval

### notifications blueprint
Responsibilities:
- notification listing
- read/unread management
- deletion and cleanup operations

### calendar blueprint
Responsibilities:
- event creation and management
- calendar query operations

### messaging blueprint
Responsibilities:
- channel and message operations
- real-time conversation support

### reports blueprint
Responsibilities:
- report creation and retrieval
- report listing and summary data access

### analytics blueprint
Responsibilities:
- dashboard and workload analytics
- operational reporting queries

### admin blueprint
Responsibilities:
- role and permission administration
- activity log review
- organization-level administrative features

## 6. Service Layer

The service layer should contain the business logic and should not be embedded directly in the route handlers.

### Why this matters
- keeps routes thin and focused on HTTP concerns
- makes business logic easier to test
- improves reuse for Celery workers and WebSocket handlers
- separates authorization and validation rules from transport logic

### Planned services
- `AuthService`
- `UserService`
- `OrganizationService`
- `TeamService`
- `ProjectService`
- `TaskService`
- `CommentService`
- `FileService`
- `NotificationService`
- `CalendarService`
- `MessagingService`
- `ReportService`
- `AnalyticsService`
- `AdminService`

Each service should coordinate:
- validation
- authorization checks
- repository calls
- event emission
- notification publishing
- activity logging

## 7. Repository Layer

The repository layer should sit between the services and SQLAlchemy.

### Responsibility
- encapsulate SQLAlchemy query logic
- keep service code from depending on raw ORM details
- provide reusable database access patterns
- centralize transaction boundaries and query composition

### Flow
Route -> Service -> Repository -> SQLAlchemy -> PostgreSQL

### Design considerations
- repositories should be focused on data access
- transaction handling should remain coordinated by services or a unit-of-work boundary
- repositories should be easy to mock for tests

## 8. Model Layer

The model layer should mirror the detailed schema documented in the database phase.

### Planned SQLAlchemy model modules
- `User`
- `Organization`
- `OrganizationMembership`
- `Role`
- `Permission`
- `RolePermission`
- `Team`
- `TeamMembership`
- `Project`
- `ProjectMembership`
- `Task`
- `Subtask`
- `Comment`
- `Attachment`
- `Notification`
- `Channel`
- `Message`
- `ActivityLog`
- `Report`
- `CalendarEvent`

The model organization should follow the rule that every tenant-scoped entity is connected to an organization context.

## 9. Schema and Validation Layer

The backend should use a dedicated validation and serialization layer.

### Recommended approach
- request validation handled before service invocation
- response serialization performed near the blueprint boundary
- type validation and field constraints enforced consistently

### Why this is useful
- prevents invalid data from entering the service layer
- standardizes API responses
- ensures compatibility with the documented API conventions

## 10. Authentication Architecture

The authentication flow should follow the planned API design.

### Flow
Registration -> Email Verification -> Login -> Access Token -> Refresh Token -> Authenticated Request -> Token Refresh -> Logout

### Responsibilities
- `AuthService` handles registration, login, token issuance, refresh, logout, and password recovery
- password hashing should occur before persistence
- JWT access tokens should be short-lived
- refresh tokens should be revocable and rotated where appropriate
- authentication checks should be enforced centrally using decorators or middleware

## 11. Authorization Architecture

Authorization should be implemented using RBAC and organization/project-level access control.

### Resolution chain
User -> Organization membership -> Role -> Permission -> Resource ownership/access

### Access model
- organization membership grants tenant-level context
- role and permission determine what actions are allowed
- project or team membership narrows access within an organization
- resource ownership may grant specific write permissions

This should remain consistent with the RBAC documentation already produced.

## 12. Transaction Management

The backend should treat certain operations as atomic units.

### Conceptual examples
- Create project
  - create project row
  - add owner membership
  - create activity log
  - commit all changes together

### Transaction guidelines
- wrap multi-step business operations in a transaction
- rollback on validation or persistence failure
- avoid partial writes for critical operations
- ensure activity log and audit entries are persisted as part of the same logical transaction where possible

## 13. Error Handling

The backend should use centralized error handling so all API endpoints return consistent errors.

### Recommended error categories
- validation errors
- authentication errors
- authorization errors
- resource not found
- conflict or duplicate state
- database errors
- unexpected server errors

### Response consistency
Errors should follow the documented API conventions and include:
- error code
- human-readable message
- optional field-level details

## 14. Redis Architecture

Redis should be used selectively and intentionally.

### Likely uses
- caching for frequently accessed data
- temporary token/session state where needed
- rate limiting support
- Celery broker support
- lightweight real-time helper state

### Avoid overuse
Redis should not be used for primary transactional persistence. PostgreSQL remains the source of truth.

## 15. Celery Architecture

Celery should handle asynchronous background tasks.

### Proposed task categories
- email notifications
- reminder jobs
- report generation
- cleanup and maintenance jobs
- future AI processing

### Flow
Flask API -> Celery -> Redis -> Worker

## 16. WebSocket Architecture

Flask-SocketIO should be used for real-time collaboration features.

### Planned capabilities
- real-time messaging
- task update notifications
- project activity feeds
- user presence indicators

### Flow
Client -> WebSocket -> SocketIO -> Application Services -> Database

### Security expectations
- WebSocket connections should require authentication
- authorization should be checked before joining channels or receiving sensitive events

## 17. File Storage Architecture

The backend should abstract file storage from the database model.

### Design direction
- the database stores metadata about uploaded files
- the storage provider handles physical file persistence

### Planned providers
- local filesystem for development
- object storage in production

## 18. Configuration Design

Configuration will be environment driven and should support development, testing, and production modes.

### Planned environment variables
- `FLASK_ENV`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `FILE_STORAGE`
- `MAIL_SERVER`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`

## 19. Logging and Observability

The backend should produce two distinct types of logs:

### Application logs
- request logs
- error logs
- performance logs
- service-level logs

### Activity/Audit logs
- stored in PostgreSQL for business auditing
- tied to users, organizations, entities, and actions

## 20. Testing Architecture

The backend should support layered testing in the future.

### Planned test structure
```text
tests/
├── unit/
├── integration/
├── api/
├── websocket/
└── fixtures/
```

### Planned test categories
- unit tests for services and repositories
- integration tests for database and transaction behavior
- API tests for endpoints and permissions
- WebSocket tests for real-time features
- authentication and authorization tests

## 21. Backend Execution Flow

A typical request should follow this path:

1. Client sends an HTTP request to a Flask blueprint
2. Blueprint validates request input
3. Blueprint delegates to a service
4. Service checks authorization and business rules
5. Repository reads or writes to PostgreSQL
6. Activity logs and notifications may be emitted
7. Response is serialized and returned to the client
