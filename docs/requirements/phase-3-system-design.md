# Phase 3 — System Design for PMS

## 1. Design Objectives

The Project Management System (PMS) will be designed as a multi-tenant SaaS platform for organizations that need structured collaboration, task execution, reporting, and real-time updates.

### Architectural goals
- Support secure organization-level isolation.
- Provide role-based access control for users, teams, projects, and tasks.
- Keep the system extensible for future AI-assisted features.
- Separate domain logic from infrastructure concerns.
- Maintain auditable operations through activity logging.

## 2. Recommended Architecture

### Application layers
1. Presentation layer
   - HTML, CSS, JavaScript, Bootstrap 5
   - Chart.js for dashboards and reporting visuals
2. Application layer
   - Flask application with modular blueprints
   - SQLAlchemy ORM for persistence
   - Flask-SocketIO for real-time collaboration
3. Data layer
   - PostgreSQL for transactional data
   - Redis for caching, queues, and session support
   - Celery for background jobs
4. Infrastructure layer
   - Docker and Docker Compose for local deployment
   - Nginx as reverse proxy
   - GitHub Actions for CI/CD

## 3. Core Design Principles

- Multi-tenancy: every tenant-scoped record must belong to an organization.
- RBAC: roles and permissions control access to organizations, projects, teams, and tasks.
- Auditability: create, update, delete, and assignment actions are logged.
- Referential integrity: foreign keys are mandatory for all dependent relationships.
- Scalability: background tasks are handled asynchronously through Celery.
- Observability: activity logs and notifications provide operational visibility.

## 4. Domain Model Summary

The system will be centered around:
- Organizations as the tenant boundary.
- Users who belong to one or more organizations.
- Teams and projects that organize work.
- Tasks and subtasks that represent execution units.
- Comments, attachments, notifications, and calendar events that support collaboration.
- Messages and channels for internal communication.
- Activity logs and reports for traceability and analytics.

## 5. Database Strategy

### General conventions
- Use UUID primary keys for distributed-safe identity handling.
- Use PostgreSQL native constraints and foreign keys.
- Use `created_at`, `updated_at`, and `deleted_at` fields where appropriate.
- Use `organization_id` on all tenant-scoped tables.
- Use soft deletion for audit-friendly lifecycle handling.
- Store flexible metadata in `JSONB` columns where needed.

### Recommended schema boundaries
- Global identity tables: `users`, `roles`, `permissions`
- Tenant-scoped tables: `organizations`, `organization_memberships`, `teams`, `team_memberships`, `projects`, `project_memberships`, `tasks`, `subtasks`, `comments`, `attachments`, `notifications`, `calendar_events`, `channels`, `messages`, `activity_logs`, `reports`

## 6. Security and Access Model

The access model will be built around:
- Organization membership as the entry point.
- Roles assigned per organization or project context.
- Permissions assigned through role mappings.
- Project and team membership to narrow access to relevant work.

### Example permissions
- `organization.manage`
- `project.create`
- `project.update`
- `task.create`
- `task.assign`
- `comment.delete`
- `report.view`

## 7. API and UI Direction

### API design
- Use RESTful endpoints for CRUD and administrative workflows.
- Use WebSockets for notifications, task updates, and live collaboration.
- Keep API responses consistent with a standard envelope pattern.

### UI direction
- Use a dashboard-driven interface with a left navigation structure.
- Provide project, task, calendar, report, and collaboration views.
- Keep the UI modular so the backend can evolve without major frontend rewrites.

## 8. Implementation Sequence

The next implementation phase should remain strictly aligned with the documented sequence:
1. Database design
2. ERD refinement
3. System architecture documentation
4. API specification
5. UI/UX wireframe planning
6. Backend implementation
7. Frontend implementation
8. Testing
9. Dockerization
10. CI/CD
11. Kubernetes
12. AI features
