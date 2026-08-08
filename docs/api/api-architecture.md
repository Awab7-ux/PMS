# API Architecture for PMS

## 1. API Goals

The PMS API will provide a RESTful interface for managing organizations, projects, tasks, collaboration, reporting, notifications, and administration in a secure, multi-tenant SaaS environment.

The API design is intentionally aligned with the existing system design requirements:
- Multi-tenancy through organization isolation
- Role-based access control
- Auditable actions and activity tracking
- Real-time collaboration support through WebSockets
- Future readiness for analytics and AI-assisted features

## 2. API Principles

- Use RESTful resource-oriented endpoints.
- Keep responses consistent and predictable.
- Require authentication for protected resources.
- Enforce organization-scoped access for tenant data.
- Use standard HTTP verbs and status codes.
- Separate read operations from write operations where necessary.

## 3. API Domain Map

### /api/auth
Purpose:
- User registration, authentication, token management, password recovery, and email verification.

Resources:
- Users, sessions, tokens, verification requests.

Authentication requirement:
- Public for registration/login/refresh/password recovery.
- Protected for logout and account-related actions.

Authorization requirement:
- Only the authenticated user may manage their own session or account.

Main operations:
- Register
- Login
- Logout
- Refresh token
- Forgot password
- Reset password
- Verify email

Relationships:
- Connected to the user profile and organization membership lifecycle.

### /api/users
Purpose:
- Manage user accounts, profile data, and account-related visibility.

Resources:
- User profiles and account metadata.

Authentication requirement:
- Required.

Authorization requirement:
- Users may view their own profile; administrators may manage other users within the organization.

Main operations:
- List users
- View a user
- Update a user profile
- Disable or delete a user account

Relationships:
- Related to organization memberships, project memberships, tasks, comments, notifications, and activity logs.

### /api/organizations
Purpose:
- Manage tenant workspaces and organization-level settings.

Resources:
- Organizations, membership records, role definitions.

Authentication requirement:
- Required.

Authorization requirement:
- Organization owners/admins manage organization settings; members access permitted resources.

Main operations:
- Create organization
- View organization details
- Update organization settings
- Delete or archive organization

Relationships:
- Parent to teams, projects, channels, reports, notifications, and calendar events.

### /api/teams
Purpose:
- Organize users into collaborative work groups.

Resources:
- Teams and team memberships.

Authentication requirement:
- Required.

Authorization requirement:
- Organization or project administrators may manage teams; members may view permitted team data.

Main operations:
- Create team
- List teams
- View team
- Update team
- Delete team
- Add/remove team members

Relationships:
- Related to organizations, projects, users, and task assignment context.

### /api/projects
Purpose:
- Manage work containers for projects and project-level collaboration.

Resources:
- Projects, project memberships, project metadata.

Authentication requirement:
- Required.

Authorization requirement:
- Allowed to organization members with project access.

Main operations:
- Create project
- List projects
- View project details
- Update project
- Delete or archive project
- Manage project memberships

Relationships:
- Parent to tasks, reports, calendar events, channels, and attachments.

### /api/tasks
Purpose:
- Manage work items and task lifecycle operations.

Resources:
- Tasks, subtasks, task assignments, task changes.

Authentication requirement:
- Required.

Authorization requirement:
- Users need project access and relevant task permissions.

Main operations:
- Create task
- List tasks
- View task details
- Update task status and details
- Delete or archive task
- Assign users

Relationships:
- Related to projects, subtasks, comments, attachments, notifications, and activity logs.

### /api/comments
Purpose:
- Handle task or project discussion threads.

Resources:
- Comments and threaded replies.

Authentication requirement:
- Required.

Authorization requirement:
- Users with access to the parent task or project may create or view comments.

Main operations:
- Create comment
- List comments
- View comment
- Update comment
- Delete comment

Relationships:
- Related to tasks, users, and notifications.

### /api/files
Purpose:
- Manage uploaded files attached to work items and project artifacts.

Resources:
- File metadata and storage references.

Authentication requirement:
- Required.

Authorization requirement:
- Access depends on project, task, or organization permissions.

Main operations:
- Upload file
- List files
- Download file metadata or content
- Update file metadata
- Delete file

Relationships:
- Related to tasks, projects, comments, and users.

### /api/notifications
Purpose:
- Provide in-app and system notification operations.

Resources:
- Notifications and read-state updates.

Authentication requirement:
- Required.

Authorization requirement:
- Users can view and manage their own notifications.

Main operations:
- List notifications
- View notification
- Mark as read
- Delete notification
- Clear all notifications

Relationships:
- Related to users, tasks, projects, and comments.

### /api/calendar
Purpose:
- Manage calendar events, deadlines, milestones, and meetings.

Resources:
- Calendar events.

Authentication requirement:
- Required.

Authorization requirement:
- Based on organization and project access.

Main operations:
- Create event
- List events
- View event
- Update event
- Delete event

Relationships:
- Related to organizations, projects, users, and reports.

### /api/messages
Purpose:
- Support channel- and project-based internal communications.

Resources:
- Channels and messages.

Authentication requirement:
- Required.

Authorization requirement:
- Based on channel membership and project access.

Main operations:
- List channels
- Create message
- Retrieve message history
- Update message
- Delete message

Relationships:
- Related to users, organizations, projects, and real-time collaboration.

### /api/reports
Purpose:
- Expose reporting and summary generation endpoints.

Resources:
- Reports and generated summaries.

Authentication requirement:
- Required.

Authorization requirement:
- Report visibility depends on organization and project permissions.

Main operations:
- Generate report
- List reports
- View report
- Delete report

Relationships:
- Related to organizations, projects, users, and analytics.

### /api/analytics
Purpose:
- Provide dashboard and analytical insights.

Resources:
- Metrics, trends, workload summaries, and dashboard data.

Authentication requirement:
- Required.

Authorization requirement:
- Limited to authorized organizational or project stakeholders.

Main operations:
- Fetch dashboard metrics
- Fetch project progress analytics
- Fetch workload analytics
- Fetch activity summaries

Relationships:
- Related to tasks, projects, users, reports, and notifications.

### /api/admin
Purpose:
- Support privileged administrative operations.

Resources:
- System-level or organization-level administrative controls.

Authentication requirement:
- Required.

Authorization requirement:
- Restricted to owners/admins only.

Main operations:
- Manage roles and permissions
- Manage organization-level memberships
- Review activity logs
- Manage platform-wide settings where applicable

Relationships:
- Related to users, organizations, projects, roles, and audit logs.
