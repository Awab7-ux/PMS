# Indexing Strategy

## 1. Indexing Goals

The indexing strategy should optimize the most common operations in the PMS platform without over-indexing every column.

The highest-value query patterns are:
- user authentication and lookup
- organization lookup and membership validation
- project and task retrieval by tenant and status
- assignee-based task queries
- notification retrieval by user and read state
- message history retrieval by channel
- activity log retrieval by actor and time

## 2. Core Index Recommendations

### users
Recommended indexes:
- `idx_users_email` on `email`
- `idx_users_username` on `username`
- `idx_users_is_active` on `is_active`

Why:
- Authentication and profile lookup rely heavily on email and username.

### organizations
Recommended indexes:
- `idx_organizations_slug` on `slug`
- `idx_organizations_is_active` on `is_active`

Why:
- Organization lookup is commonly done by slug.

### organization_memberships
Recommended indexes:
- `idx_org_memberships_org_user` on `(organization_id, user_id)`
- `idx_org_memberships_user` on `user_id`

Why:
- Membership validation is a frequent authorization check.

### teams
Recommended indexes:
- `idx_teams_org` on `organization_id`
- `idx_teams_lead_user` on `lead_user_id`

Why:
- Team listing and scoped management usually filter by organization.

### team_memberships
Recommended indexes:
- `idx_team_memberships_team_user` on `(team_id, user_id)`
- `idx_team_memberships_user` on `user_id`

Why:
- Team membership lookups are common during team-based access checks.

### projects
Recommended indexes:
- `idx_projects_org` on `organization_id`
- `idx_projects_owner` on `owner_user_id`
- `idx_projects_status` on `status`
- `idx_projects_org_status` on `(organization_id, status)`

Why:
- Projects are usually retrieved in the tenant context and by lifecycle state.

### project_memberships
Recommended indexes:
- `idx_project_memberships_project_user` on `(project_id, user_id)`
- `idx_project_memberships_user` on `user_id`

Why:
- Membership checks are central to project access enforcement.

### tasks
Recommended indexes:
- `idx_tasks_org_project` on `(organization_id, project_id)`
- `idx_tasks_assignee` on `assignee_id`
- `idx_tasks_status` on `status`
- `idx_tasks_due_date` on `due_date`
- `idx_tasks_org_status_assignee` on `(organization_id, status, assignee_id)`

Why:
- Task dashboards and backlog views often filter by organization, project, assignee, status, and due date.

### subtasks
Recommended indexes:
- `idx_subtasks_task` on `task_id`
- `idx_subtasks_assignee` on `assignee_id`

Why:
- Subtasks are normally queried as children of a parent task.

### comments
Recommended indexes:
- `idx_comments_task` on `task_id`
- `idx_comments_user` on `user_id`
- `idx_comments_org` on `organization_id`

Why:
- Comments are often pulled in task conversation views.

### attachments
Recommended indexes:
- `idx_attachments_task` on `task_id`
- `idx_attachments_uploader` on `uploaded_by`
- `idx_attachments_org` on `organization_id`

Why:
- File listings usually require parent-task context and uploader filtering.

### channels
Recommended indexes:
- `idx_channels_org` on `organization_id`
- `idx_channels_project` on `project_id`

Why:
- Channel lookup is mostly tenant- and project-scoped.

### messages
Recommended indexes:
- `idx_messages_channel_created` on `(channel_id, created_at)`
- `idx_messages_user` on `user_id`

Why:
- Message history is typically retrieved chronologically by channel.

### notifications
Recommended indexes:
- `idx_notifications_user_created` on `(user_id, created_at)`
- `idx_notifications_is_read` on `(user_id, is_read)`

Why:
- Notification inbox views require recent and unread filtering.

### calendar_events
Recommended indexes:
- `idx_calendar_org_start` on `(organization_id, start_at)`
- `idx_calendar_project` on `project_id`

Why:
- Calendar views often filter by organization and date range.

### activity_logs
Recommended indexes:
- `idx_activity_org_created` on `(organization_id, created_at)`
- `idx_activity_user_created` on `(user_id, created_at)`
- `idx_activity_entity` on `(entity_type, entity_id)`

Why:
- Auditing and review flows need recent activity and entity-based lookups.

### reports
Recommended indexes:
- `idx_reports_org_generated` on `(organization_id, generated_at)`
- `idx_reports_project` on `project_id`

Why:
- Reporting views usually need recent report history within a tenant.

## 3. Indexing Principles

- Avoid indexing every column blindly.
- Focus on foreign keys, tenant identifiers, status filters, assignee filters, date filters, and common join paths.
- Prefer composite indexes for the most frequent multi-column filters.
- Keep write-heavy tables balanced with the need for read performance.
- Review indexes after the first query patterns are observed in development.
