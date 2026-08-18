# Project Management System (PMS)

## Current Phase

**Requirements Analysis + Mermaid Use Case Diagrams + Documentation**

This phase covers requirements analysis and UML use case modeling only. No
application or business logic (ERD, database, backend, frontend, Docker,
Kubernetes, or AI implementation) has been implemented yet.

# System Diagrams

The system's use case diagrams are maintained as [Mermaid](https://mermaid.js.org/)
source files under `docs/diagrams/`, so they stay version-controlled, diffable,
and easy to update alongside the codebase. Each `.mmd` file can be rendered
with the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (`mmdc`) or
any Mermaid-compatible viewer (e.g. the Mermaid Live Editor, GitHub/GitLab
native Mermaid preview, or VS Code's Mermaid extension).

| # | Diagram | Source |
|---|---------|--------|
| 1 | System-Wide Use Case Diagram | [`docs/diagrams/system-use-case.mmd`](docs/diagrams/system-use-case.mmd) |
| 2 | Authentication | [`docs/diagrams/authentication-use-case.mmd`](docs/diagrams/authentication-use-case.mmd) |
| 3 | Organization & User Management | [`docs/diagrams/organization-user-management-use-case.mmd`](docs/diagrams/organization-user-management-use-case.mmd) |
| 4 | Project & Task Management | [`docs/diagrams/project-task-management-use-case.mmd`](docs/diagrams/project-task-management-use-case.mmd) |
| 5 | Communication & Notifications | [`docs/diagrams/communication-notifications-use-case.mmd`](docs/diagrams/communication-notifications-use-case.mmd) |
| 6 | Reports, Analytics & Administration | [`docs/diagrams/reports-analytics-administration-use-case.mmd`](docs/diagrams/reports-analytics-administration-use-case.mmd) |

Rendered SVG/PNG copies (when available) live under
`docs/diagrams/rendered/`, using the same filename as their source.

## Diagram 1 — System-Wide Use Case Diagram
Shows all five actors (Super Admin, Organization Owner, Project Manager, Team
Member, Client) and their major interactions across the PMS's core modules.

## Diagram 2 — Authentication
Covers Register, Login, Logout, Verify Email, Reset Password, Change
Password, JWT Authentication, Refresh Token, and Role-Based Access Control,
and which actors use each.

## Diagram 3 — Organization & User Management
Details organization and user administration (create/edit organizations,
invite/remove members, assign roles, suspend/activate users, manage teams)
and how permissions differ across the five actor types.

## Diagram 4 — Project & Task Management
Covers project lifecycle, task management (including subtasks, comments,
attachments), and the Kanban board (drag-and-drop, filtering, search), with
`<<include>>`/`<<extend>>` relationships between related use cases.

## Diagram 5 — Communication & Notifications
Covers channel-based and direct messaging, file uploads, and how messaging
events trigger the various notification types (task assignment, comment,
mention, deadline, project update).

## Diagram 6 — Reports, Analytics & Administration
Separates organization-level reporting (dashboards, analytics, project/team
performance reports) from system-level administration (system statistics,
logs, and settings), and shows which actors access each.

## Rendering Status

The Mermaid source files above are complete and syntactically valid. SVG/PNG
rendering via `mmdc` (Mermaid CLI) is **pending** in this environment because
the headless Chrome dependency required by the CLI is not installed and
network access is unavailable to install it. No unrelated dependencies were
installed to work around this. To render locally:

```bash
npx @mermaid-js/mermaid-cli -i docs/diagrams/system-use-case.mmd -o docs/diagrams/rendered/system-use-case.svg
```

Repeat for each `.mmd` file, or use a Mermaid-compatible viewer to preview
the diagrams directly.
