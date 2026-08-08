# Database Design for PMS

## 1. Design Approach

The database is designed as a PostgreSQL-based multi-tenant platform with strong referential integrity and auditability. Every tenant-scoped entity is associated with an organization to ensure logical isolation.

## 2. Core Entity Design

### User
- Purpose: Represents a human account that can authenticate, create work, and participate in organizations.
- Primary key: `id`
- Foreign keys: None at the base level; references via membership tables.
- Important attributes: `email`, `username`, `full_name`, `password_hash`, `avatar_url`, `is_active`, `is_superuser`, `last_login_at`, `created_at`, `updated_at`
- Relationships: One user can belong to many organizations; one user can join many teams and projects; one user can create many tasks, comments, messages, and notifications.
- Cardinality: `1:N` with memberships, tasks, comments, notifications, messages, activity logs.
- Constraints: Unique email and username; non-null full name; strong password hash requirement.
- Important indexes: `idx_users_email`, `idx_users_is_active`

### Organization
- Purpose: Acts as the tenant boundary for all workspace-scoped data.
- Primary key: `id`
- Foreign keys: None.
- Important attributes: `name`, `slug`, `description`, `industry`, `settings_json`, `is_active`, `created_at`, `updated_at`
- Relationships: One organization has many users through memberships, many teams, many projects, many calendar events, and many channels.
- Cardinality: `1:N` to most tenant-scoped entities.
- Constraints: Unique slug; non-null name.
- Important indexes: `idx_org_slug`, `idx_org_is_active`

### OrganizationMembership
- Purpose: Links a user to an organization and stores their role and status inside that tenant.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `user_id -> users.id`, `role_id -> roles.id`
- Important attributes: `status`, `joined_at`, `left_at`, `invited_by`, `is_owner`
- Relationships: Many users belong to many organizations through this table.
- Cardinality: `N:M` between users and organizations.
- Constraints: Unique pair `(organization_id, user_id)`; `status` limited to active/pending/removed.
- Important indexes: `idx_org_membership_user`, `idx_org_membership_org`

### Role
- Purpose: Defines a reusable role within an organization.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id` (optional for tenant-scoped roles)
- Important attributes: `name`, `description`, `is_system_default`, `created_at`
- Relationships: One role can be assigned to many memberships.
- Cardinality: `1:N` to organization memberships.
- Constraints: Unique role name per organization; system roles must be immutable where appropriate.
- Important indexes: `idx_roles_org`

### Permission
- Purpose: Represents an atomic access right used by the RBAC model.
- Primary key: `id`
- Foreign keys: None.
- Important attributes: `code`, `description`
- Relationships: Many permissions can be assigned to many roles through a role-permission mapping table.
- Cardinality: `N:M` with roles.
- Constraints: Unique code.
- Important indexes: `idx_permissions_code`

### Team
- Purpose: Groups users for coordination around a subset of work within an organization.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `lead_user_id -> users.id`
- Important attributes: `name`, `description`, `is_active`, `created_at`
- Relationships: One organization has many teams; one team has many members and many projects may be associated by context.
- Cardinality: `1:N` to team memberships.
- Constraints: Unique team name per organization; lead user must be a member.
- Important indexes: `idx_teams_org`, `idx_teams_lead`

### TeamMembership
- Purpose: Associates users with teams.
- Primary key: `id`
- Foreign keys: `team_id -> teams.id`, `user_id -> users.id`
- Important attributes: `role_in_team`, `joined_at`
- Relationships: Many-to-many between users and teams.
- Cardinality: `N:M`.
- Constraints: Unique pair `(team_id, user_id)`.
- Important indexes: `idx_team_membership_user`, `idx_team_membership_team`

### Project
- Purpose: Represents a work container for tasks, teams, and members.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `owner_user_id -> users.id`, `parent_project_id -> projects.id` (optional for sub-projects)
- Important attributes: `name`, `code`, `description`, `status`, `start_date`, `end_date`, `progress_percent`, `created_at`, `updated_at`
- Relationships: One organization has many projects; one project has many tasks and many project memberships.
- Cardinality: `1:N` to tasks and memberships.
- Constraints: Unique project code per organization; status limited to draft/planning/active/on_hold/completed.
- Important indexes: `idx_projects_org`, `idx_projects_status`, `idx_projects_owner`

### ProjectMembership
- Purpose: Defines user access to a specific project.
- Primary key: `id`
- Foreign keys: `project_id -> projects.id`, `user_id -> users.id`, `role_id -> roles.id`
- Important attributes: `access_level`, `joined_at`
- Relationships: Many users can be assigned to many projects.
- Cardinality: `N:M`.
- Constraints: Unique pair `(project_id, user_id)`.
- Important indexes: `idx_project_membership_project`, `idx_project_membership_user`

### Task
- Purpose: Represents a specific work item assigned to a user or team.
- Primary key: `id`
- Foreign keys: `project_id -> projects.id`, `organization_id -> organizations.id`, `assignee_id -> users.id`, `reporter_id -> users.id`, `parent_task_id -> tasks.id` (optional for nested tasks)
- Important attributes: `title`, `description`, `priority`, `status`, `due_date`, `estimated_hours`, `actual_hours`, `progress_percent`, `created_at`, `updated_at`
- Relationships: One project has many tasks; one task may have many subtasks and comments; one user can be assigned many tasks.
- Cardinality: `1:N` to subtasks and comments.
- Constraints: `status` and `priority` should use check constraints; due date must be non-null when needed.
- Important indexes: `idx_tasks_project`, `idx_tasks_assignee`, `idx_tasks_status`, `idx_tasks_due_date`

### Subtask
- Purpose: Breaks a large task into smaller execution units.
- Primary key: `id`
- Foreign keys: `task_id -> tasks.id`, `assignee_id -> users.id`
- Important attributes: `title`, `description`, `status`, `due_date`, `created_at`
- Relationships: One parent task has many subtasks.
- Cardinality: `1:N`.
- Constraints: Subtask cannot be orphaned from its parent task.
- Important indexes: `idx_subtasks_task`, `idx_subtasks_assignee`

### Comment
- Purpose: Stores discussion and collaboration notes on tasks or projects.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `task_id -> tasks.id`, `user_id -> users.id`, `parent_comment_id -> comments.id` (optional)
- Important attributes: `body`, `created_at`, `updated_at`
- Relationships: One task has many comments; one user writes many comments.
- Cardinality: `1:N`.
- Constraints: Comments should be non-empty and linked to an existing task or parent entity.
- Important indexes: `idx_comments_task`, `idx_comments_user`

### Attachment
- Purpose: Stores uploaded files related to tasks, projects, or comments.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `task_id -> tasks.id`, `uploaded_by -> users.id`
- Important attributes: `file_name`, `file_path`, `mime_type`, `file_size_bytes`, `created_at`
- Relationships: One task can have many attachments; one user can upload many attachments.
- Cardinality: `1:N`.
- Constraints: File name and storage path must be non-null.
- Important indexes: `idx_attachments_task`, `idx_attachments_user`

### Notification
- Purpose: Delivers user-facing alerts for changes, mentions, deadlines, or assignments.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `user_id -> users.id`
- Important attributes: `type`, `title`, `body`, `is_read`, `created_at`, `read_at`
- Relationships: One user receives many notifications.
- Cardinality: `1:N`.
- Constraints: Notification type should be constrained to known values.
- Important indexes: `idx_notifications_user`, `idx_notifications_is_read`

### CalendarEvent
- Purpose: Stores milestones, meetings, deadlines, and milestones for projects or organizations.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `project_id -> projects.id`, `created_by -> users.id`
- Important attributes: `title`, `description`, `start_at`, `end_at`, `location`, `event_type`, `created_at`
- Relationships: One organization has many events; events may be linked to a project.
- Cardinality: `1:N` to projects and organizations.
- Constraints: End time must be after start time.
- Important indexes: `idx_calendar_org`, `idx_calendar_start_at`

### Channel
- Purpose: Groups messages for a project team, organization, or topic-based discussion.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `project_id -> projects.id` (optional)
- Important attributes: `name`, `channel_type`, `is_private`, `created_at`
- Relationships: One organization has many channels; one project may have many channels.
- Cardinality: `1:N` to messages.
- Constraints: Channel type should be limited to known values.
- Important indexes: `idx_channels_org`, `idx_channels_project`

### Message
- Purpose: Stores chat or discussion messages within a channel.
- Primary key: `id`
- Foreign keys: `channel_id -> channels.id`, `user_id -> users.id`
- Important attributes: `body`, `created_at`, `updated_at`
- Relationships: One channel has many messages; one user sends many messages.
- Cardinality: `1:N`.
- Constraints: Message body must be non-empty.
- Important indexes: `idx_messages_channel`, `idx_messages_user`

### ActivityLog
- Purpose: Records important actions for auditability and monitoring.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `user_id -> users.id`
- Important attributes: `entity_type`, `entity_id`, `action`, `metadata_json`, `created_at`
- Relationships: One user can have many activity records; one organization records many events.
- Cardinality: `1:N`.
- Constraints: Action should be constrained to permitted verbs; metadata stored as JSONB for flexibility.
- Important indexes: `idx_activity_org`, `idx_activity_user`, `idx_activity_created_at`

### Report
- Purpose: Stores generated analytics or summary reports for projects or organizations.
- Primary key: `id`
- Foreign keys: `organization_id -> organizations.id`, `project_id -> projects.id`, `generated_by -> users.id`
- Important attributes: `report_type`, `title`, `summary_json`, `generated_at`
- Relationships: One organization can generate many reports; one project can have many reports.
- Cardinality: `1:N`.
- Constraints: Report type should be constrained to approved values.
- Important indexes: `idx_reports_org`, `idx_reports_project`

## 3. Relationship Summary

- One organization owns many teams, projects, channels, events, notifications, and activity records.
- One user may be a member of many organizations and many projects.
- One project contains many tasks and may be linked to many calendar events and reports.
- One task may have many subtasks, comments, and attachments.
- One organization may host many collaboration channels and messages.

## 4. Recommended PostgreSQL Constraints

- Use foreign keys with `ON DELETE CASCADE` for tenant-scoped child records when the parent organization is removed.
- Use `CHECK` constraints for status, priority, and date validity.
- Use unique constraints for membership and naming rules.
- Use `NOT NULL` for mandatory business fields.
- Use `JSONB` for flexible metadata while preserving querying capability.

## 5. Recommended Indexing Strategy

- Index foreign keys and tenant identifiers (`organization_id`).
- Index common lookup fields such as `status`, `assignee_id`, `due_date`, `created_at`, and `is_read`.
- Add composite indexes for common query patterns such as project + status + assignee.
