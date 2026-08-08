# Detailed Database Schema Design

## 1. Schema Design Principles

The detailed schema below is aligned with the existing PMS requirements, ERD, API design, RBAC model, and security architecture.

### Design decisions
- Use UUID primary keys for most tables to support distributed-safe identity and future SaaS scaling.
- Use PostgreSQL-native `TIMESTAMPTZ` for timestamps.
- Use `VARCHAR` with `CHECK` constraints for status and priority values instead of PostgreSQL enum types, because this is easier to evolve with future business changes.
- Use soft deletion through `deleted_at` for most tenant-scoped records.
- Use `organization_id` on all tenant-scoped tables to enforce multi-tenancy.
- Use `JSONB` for flexible metadata fields where the schema may evolve.

## 2. Primary Key Strategy

### Recommendation: UUID primary keys

| Aspect | Decision |
| --- | --- |
| Primary key type | `UUID` |
| Why | Better fit for distributed SaaS systems and safer external references than auto-incrementing integers |
| PostgreSQL compatibility | Fully supported with `UUID` and `gen_random_uuid()` or `uuid_generate_v4()` |
| SQLAlchemy compatibility | Supported natively via `UUID` columns and Python `uuid.UUID` types |
| Security | Less predictable than sequential integers |
| Index implications | Slightly larger storage footprint, but still efficient with proper indexing |

## 3. Core Tables

### users
Purpose: Stores the core identity of each human account.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Unique user identifier |
| email | VARCHAR(255) | NO | UNIQUE | | Unique email address |
| username | VARCHAR(100) | NO | UNIQUE | | Unique username |
| full_name | VARCHAR(255) | NO | | | Display name |
| password_hash | VARCHAR(255) | NO | | | Hashed password |
| avatar_url | TEXT | YES | | | Optional profile image |
| is_active | BOOLEAN | NO | | true | Account enabled flag |
| is_superuser | BOOLEAN | NO | | false | Platform administrator flag |
| last_login_at | TIMESTAMPTZ | YES | | | Last successful login |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `email` and `username` must be unique.
- `full_name` must not be empty.

Relationships:
- One user can belong to many organizations via `organization_memberships`.
- One user can belong to many teams via `team_memberships`.
- One user can join many projects via `project_memberships`.

### organizations
Purpose: Represents the tenant workspace boundary.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Unique organization identifier |
| name | VARCHAR(255) | NO | | | Organization name |
| slug | VARCHAR(100) | NO | UNIQUE | | URL-friendly organization slug |
| description | TEXT | YES | | | Organization summary |
| industry | VARCHAR(100) | YES | | | Optional industry |
| settings_json | JSONB | YES | | '{}' | Tenant-specific settings |
| is_active | BOOLEAN | NO | | true | Organization active flag |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `slug` must be unique.
- `name` must not be empty.

Relationships:
- One organization has many teams, projects, channels, calendar events, notifications, and activity logs.

### roles
Purpose: Defines reusable roles within an organization.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Unique role identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| name | VARCHAR(100) | NO | | | Role name |
| description | TEXT | YES | | | Role description |
| is_system_default | BOOLEAN | NO | | false | Indicates built-in role |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- Unique `(organization_id, name)`.
- `name` should be non-empty.

Relationships:
- One role belongs to one organization and can be assigned to many memberships.

### permissions
Purpose: Stores atomic permissions used by the RBAC model.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Unique permission identifier |
| code | VARCHAR(100) | NO | UNIQUE | | Permission code such as `project.create` |
| description | TEXT | YES | | | Permission description |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |

Relationships:
- Many permissions can be assigned to many roles through `role_permissions`.

### role_permissions
Purpose: Many-to-many mapping between roles and permissions.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| role_id | UUID | NO | FK -> roles.id | | Role reference |
| permission_id | UUID | NO | FK -> permissions.id | | Permission reference |
| created_at | TIMESTAMPTZ | NO | | now() | Assignment timestamp |

Constraints:
- Composite primary key `(role_id, permission_id)`.

### organization_memberships
Purpose: Connects users to organizations and stores their membership state and role.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Membership identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Organization reference |
| user_id | UUID | NO | FK -> users.id | | User reference |
| role_id | UUID | NO | FK -> roles.id | | Effective role inside the organization |
| status | VARCHAR(20) | NO | | 'active' | Membership status |
| invited_by | UUID | YES | FK -> users.id | | User who invited the member |
| is_owner | BOOLEAN | NO | | false | Marks organization owner |
| joined_at | TIMESTAMPTZ | NO | | now() | Join timestamp |
| left_at | TIMESTAMPTZ | YES | | | Leave timestamp |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |

Constraints:
- Unique `(organization_id, user_id)`.
- `status` must be one of `active`, `pending`, `removed`.

Relationships:
- Many-to-many join table between organizations and users.

### teams
Purpose: Groups users for collaboration around a subset of work.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Team identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| lead_user_id | UUID | YES | FK -> users.id | | Team lead |
| name | VARCHAR(255) | NO | | | Team name |
| description | TEXT | YES | | | Team description |
| is_active | BOOLEAN | NO | | true | Team active flag |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- Unique `(organization_id, name)`.

Relationships:
- One organization has many teams.
- One team has many memberships.

### team_memberships
Purpose: Associates users with teams.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Membership identifier |
| team_id | UUID | NO | FK -> teams.id | | Team reference |
| user_id | UUID | NO | FK -> users.id | | User reference |
| role_in_team | VARCHAR(50) | YES | | 'member' | Team-specific role |
| joined_at | TIMESTAMPTZ | NO | | now() | Join timestamp |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |

Constraints:
- Unique `(team_id, user_id)`.

### projects
Purpose: Represents a work container for tasks, teams, and members.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Project identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| owner_user_id | UUID | NO | FK -> users.id | | Project owner |
| parent_project_id | UUID | YES | FK -> projects.id | | Optional parent project |
| name | VARCHAR(255) | NO | | | Project name |
| code | VARCHAR(50) | YES | | | Project code or short identifier |
| description | TEXT | YES | | | Project description |
| status | VARCHAR(30) | NO | | 'Planning' | Project status |
| start_date | DATE | YES | | | Planned start date |
| end_date | DATE | YES | | | Planned end date |
| progress_percent | INTEGER | NO | | 0 | Completion percentage |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- Unique `(organization_id, code)` when `code` is present.
- `status` must be one of `Planning`, `Active`, `On Hold`, `Completed`, `Cancelled`.

Relationships:
- One organization has many projects.
- One project has many tasks, memberships, calendar events, reports, and channels.

### project_memberships
Purpose: Defines user access to a specific project.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Membership identifier |
| project_id | UUID | NO | FK -> projects.id | | Project reference |
| user_id | UUID | NO | FK -> users.id | | User reference |
| role_id | UUID | NO | FK -> roles.id | | Role in project context |
| access_level | VARCHAR(50) | NO | | 'member' | Access level |
| joined_at | TIMESTAMPTZ | NO | | now() | Join timestamp |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |

Constraints:
- Unique `(project_id, user_id)`.

### tasks
Purpose: Represents a planned or in-progress task assigned to a user or team.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Task identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| project_id | UUID | NO | FK -> projects.id | | Parent project |
| assignee_id | UUID | YES | FK -> users.id | | Assigned user |
| reporter_id | UUID | NO | FK -> users.id | | Task creator |
| parent_task_id | UUID | YES | FK -> tasks.id | | Optional parent task |
| title | VARCHAR(255) | NO | | | Task title |
| description | TEXT | YES | | | Detailed description |
| status | VARCHAR(30) | NO | | 'Backlog' | Task status |
| priority | VARCHAR(20) | NO | | 'Medium' | Task priority |
| due_date | DATE | YES | | | Due date |
| estimated_hours | NUMERIC(6,2) | YES | | | Estimated effort |
| actual_hours | NUMERIC(6,2) | YES | | | Actual effort |
| progress_percent | INTEGER | NO | | 0 | Completion percentage |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `status` must be one of `Backlog`, `To Do`, `In Progress`, `In Review`, `Testing`, `Done`.
- `priority` must be one of `Low`, `Medium`, `High`, `Critical`.

Relationships:
- Many tasks belong to a project.
- A task may have many subtasks, comments, and attachments.

### subtasks
Purpose: Breaks a larger task into smaller units.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Subtask identifier |
| task_id | UUID | NO | FK -> tasks.id | | Parent task |
| assignee_id | UUID | YES | FK -> users.id | | Assigned user |
| title | VARCHAR(255) | NO | | | Subtask title |
| description | TEXT | YES | | | Subtask description |
| status | VARCHAR(30) | NO | | 'Backlog' | Subtask status |
| due_date | DATE | YES | | | Subtask due date |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `status` uses the same allowed values as tasks.

### comments
Purpose: Stores discussion related to tasks or work items.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Comment identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| task_id | UUID | NO | FK -> tasks.id | | Parent task |
| user_id | UUID | NO | FK -> users.id | | Author |
| parent_comment_id | UUID | YES | FK -> comments.id | | Optional reply reference |
| body | TEXT | NO | | | Comment text |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `body` must not be empty.

### attachments
Purpose: Stores metadata for uploaded files without saving binary content directly in the database.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Attachment identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| task_id | UUID | YES | FK -> tasks.id | | Related task |
| uploaded_by | UUID | NO | FK -> users.id | | Uploader |
| file_name | VARCHAR(255) | NO | | | Original file name |
| storage_key | TEXT | NO | | | Storage path or object key |
| storage_provider | VARCHAR(50) | NO | | 'local' | Storage backend |
| mime_type | VARCHAR(100) | YES | | | MIME type |
| file_size_bytes | BIGINT | YES | | | File size |
| sha256 | VARCHAR(64) | YES | | | Optional checksum |
| created_at | TIMESTAMPTZ | NO | | now() | Upload timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `file_name` and `storage_key` must be present.
- `file_size_bytes` should be non-negative.

### channels
Purpose: Groups messages for organization, project, or team collaboration.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Channel identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| project_id | UUID | YES | FK -> projects.id | | Optional project association |
| name | VARCHAR(255) | NO | | | Channel name |
| channel_type | VARCHAR(30) | NO | | 'project' | Channel category |
| is_private | BOOLEAN | NO | | false | Whether access is restricted |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `channel_type` should be one of `organization`, `project`, `direct`.

Relationships:
- A channel has many messages.
- Direct messaging can be represented by a channel with `channel_type='direct'`.

### messages
Purpose: Stores messages sent inside channels.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Message identifier |
| channel_id | UUID | NO | FK -> channels.id | | Parent channel |
| user_id | UUID | NO | FK -> users.id | | Sender |
| body | TEXT | NO | | | Message content |
| is_read | BOOLEAN | NO | | false | Read state |
| read_at | TIMESTAMPTZ | YES | | | Timestamp when read |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `body` must not be empty.

### notifications
Purpose: Stores user-facing alerts about work activity.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Notification identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| user_id | UUID | NO | FK -> users.id | | Recipient |
| related_entity_type | VARCHAR(50) | YES | | | Related entity type |
| related_entity_id | UUID | YES | | | Related entity identifier |
| notification_type | VARCHAR(50) | NO | | 'info' | Notification category |
| title | VARCHAR(255) | NO | | | Notification title |
| body | TEXT | YES | | | Notification content |
| is_read | BOOLEAN | NO | | false | Read state |
| read_at | TIMESTAMPTZ | YES | | | Read timestamp |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `notification_type` should be limited to values such as `task_assigned`, `task_updated`, `comment_added`, `mention`, `deadline_reminder`, `project_update`, `message_received`.

### calendar_events
Purpose: Stores milestones, deadlines, meetings, and other time-based events.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Event identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| project_id | UUID | YES | FK -> projects.id | | Optional related project |
| created_by | UUID | NO | FK -> users.id | | Creator |
| title | VARCHAR(255) | NO | | | Event title |
| description | TEXT | YES | | | Event description |
| event_type | VARCHAR(50) | NO | | 'meeting' | Event category |
| start_at | TIMESTAMPTZ | NO | | | Start time |
| end_at | TIMESTAMPTZ | YES | | | End time |
| location | VARCHAR(255) | YES | | | Optional physical or virtual location |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| updated_at | TIMESTAMPTZ | NO | | now() | Last update timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `end_at` must be greater than or equal to `start_at` when provided.

### activity_logs
Purpose: Records important actions for auditing and operational visibility.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Activity log identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| user_id | UUID | YES | FK -> users.id | | Actor |
| entity_type | VARCHAR(100) | NO | | | Resource type |
| entity_id | UUID | YES | | | Resource identifier |
| action | VARCHAR(50) | NO | | | Action taken |
| metadata_json | JSONB | YES | | '{}' | Additional metadata |
| created_at | TIMESTAMPTZ | NO | | now() | Timestamp |

Constraints:
- `action` should be constrained to known verbs such as `create`, `update`, `delete`, `assign`, `invite`, `login`, `logout`.

### reports
Purpose: Stores generated summaries or analytics snapshots for projects and organizations.

| Column | Type | Nullable | Key | Default | Description |
| --- | --- | --- | --- | --- | --- |
| id | UUID | NO | PK | gen_random_uuid() | Report identifier |
| organization_id | UUID | NO | FK -> organizations.id | | Tenant owner |
| project_id | UUID | YES | FK -> projects.id | | Optional related project |
| generated_by | UUID | NO | FK -> users.id | | Report creator |
| report_type | VARCHAR(50) | NO | | 'summary' | Report category |
| title | VARCHAR(255) | NO | | | Report title |
| summary_json | JSONB | YES | | '{}' | Report data |
| generated_at | TIMESTAMPTZ | NO | | now() | Generation time |
| created_at | TIMESTAMPTZ | NO | | now() | Creation timestamp |
| deleted_at | TIMESTAMPTZ | YES | | | Soft delete timestamp |

Constraints:
- `report_type` should be limited to values such as `summary`, `project_progress`, `team_workload`, `organization_overview`.

## 4. Relationships Summary

| Parent | Cardinality | Child |
| --- | --- | --- |
| organizations | 1:N | teams |
| organizations | 1:N | projects |
| organizations | 1:N | organization_memberships |
| organizations | 1:N | channels |
| organizations | 1:N | notifications |
| organizations | 1:N | calendar_events |
| organizations | 1:N | activity_logs |
| organizations | 1:N | reports |
| users | 1:N | organization_memberships |
| users | 1:N | team_memberships |
| users | 1:N | project_memberships |
| users | 1:N | tasks |
| users | 1:N | comments |
| users | 1:N | notifications |
| users | 1:N | messages |
| projects | 1:N | tasks |
| projects | 1:N | project_memberships |
| projects | 1:N | calendar_events |
| projects | 1:N | reports |
| tasks | 1:N | subtasks |
| tasks | 1:N | comments |
| tasks | 1:N | attachments |
| channels | 1:N | messages |

## 5. Constraint Strategy

### Recommended constraints
- Use `NOT NULL` for mandatory business fields.
- Use `UNIQUE` for membership and naming rules.
- Use `FOREIGN KEY` for all parent-child relationships.
- Use `CHECK` constraints for status, priority, and lifecycle values.
- Use `ON DELETE RESTRICT` by default for critical relationships; `ON DELETE CASCADE` only for clearly owned child data when the parent is removed.
- Use soft delete instead of hard delete for most business records to preserve auditability.

### Notes on business rules
- Prevent duplicate organization membership with a unique constraint on `(organization_id, user_id)`.
- Prevent duplicate team membership with a unique constraint on `(team_id, user_id)`.
- Prevent duplicate project membership with a unique constraint on `(project_id, user_id)`.
- Prevent invalid statuses and priorities with `CHECK` constraints.

## 6. Audit and Timestamp Strategy

### Recommended timestamp fields
- `created_at`: set on insert
- `updated_at`: updated on changes
- `deleted_at`: nullable; indicates soft deletion

### Entities using soft deletion
- organizations
- teams
- projects
- tasks
- subtasks
- comments
- attachments
- channels
- messages
- notifications
- calendar_events
- reports

### Entities that should remain hard-delete friendly
- `role_permissions`
- `organization_memberships`
- `team_memberships`
- `project_memberships`
- `activity_logs`

## 7. Status and Priority Values

### Project status values
- `Planning`
- `Active`
- `On Hold`
- `Completed`
- `Cancelled`

### Task status values
- `Backlog`
- `To Do`
- `In Progress`
- `In Review`
- `Testing`
- `Done`

### Task priority values
- `Low`
- `Medium`
- `High`
- `Critical`

### Recommendation
Use `VARCHAR` columns with `CHECK` constraints rather than PostgreSQL enums. This keeps the schema flexible for future business changes and is straightforward for SQLAlchemy models.

## 8. File Attachment Strategy

The database should store file metadata, not the binary content itself. The storage abstraction should support:
- local filesystem storage in development
- cloud object storage in production
- a future storage service interface behind a file repository abstraction

The attachment table stores metadata such as file name, storage key, MIME type, size, uploader, and related entity.

## 9. Messaging and Notification Design

### Messaging
- Channels represent conversation containers.
- Messages belong to channels and are linked to senders.
- Direct messaging can be modeled as a channel with `channel_type='direct'`.

### Notifications
- Notifications are user-specific records for task assignments, updates, comments, mentions, deadlines, project changes, and new messages.
- A notification includes recipient, type, related entity, and read state.
