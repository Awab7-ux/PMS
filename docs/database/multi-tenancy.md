# Multi-Tenancy Design

## 1. Tenant Model

PMS is designed as a multi-organization SaaS platform. The primary tenant boundary is the organization.

Every tenant-scoped record must be associated with an `organization_id` so that data from one organization cannot be mixed with that of another.

## 2. Tenant Identification Strategy

### Primary tenant boundary
- `organizations` is the top-level tenant container.

### Tenant-scoped tables
The following tables should include `organization_id`:
- `organizations`
- `roles`
- `organization_memberships`
- `teams`
- `projects`
- `tasks`
- `comments`
- `attachments`
- `notifications`
- `channels`
- `messages`
- `calendar_events`
- `activity_logs`
- `reports`

### Global identity tables
The following are not tenant-scoped in the same way:
- `users`
- `permissions`

This means the platform identity is global, while work and collaboration data remain inside an organization boundary.

## 3. Organization Ownership

Each organization has its own owners and administrators through membership records and role assignments.

Recommended ownership rules:
- At least one organization owner exists for every organization.
- Owners can manage members, roles, teams, projects, and settings.
- Administrators can manage operational workflows but not necessarily destroy the organization.

## 4. Foreign Key and Isolation Strategy

The database should enforce access boundaries through:
- foreign keys from child records to the organization row
- membership validation in application logic
- role-based checks before performing sensitive operations

### Example isolation pattern
A task must always belong to:
- one organization
- one project inside that organization

This prevents a project or task from being created outside the intended tenant context.

## 5. Authorization Relationship

The multi-tenancy model is closely related to the RBAC model:
- organization membership determines whether a user can access the tenant
- role assignment determines what actions are permitted inside the tenant
- project membership or team membership narrows access within the organization

## 6. Data Isolation Rules

The system should enforce the following rules:
- A user cannot access another organization’s data without explicit membership.
- Project data is only visible when the user belongs to the parent organization and has project access.
- Team and task data must be scoped to the organization and the relevant project context.
- Activity logs and notifications are stored per organization and per user.

## 7. Future Scalability

The current design is suitable for an initial monolithic Flask + SQLAlchemy deployment. In the future, the following can be introduced without redesigning the model:
- database sharding by tenant
- tenant-specific schemas
- a dedicated tenancy service layer
- PostgreSQL Row-Level Security if required later

## 8. Important Note

PostgreSQL Row-Level Security is intentionally not required in this phase. The current design relies on application-level enforcement plus strict foreign keys and tenant-scoped queries.
