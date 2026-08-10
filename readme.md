# Project Management System (PMS)

A production-oriented full-stack Project Management SaaS built with **Flask**, **PostgreSQL**, **React**, and **Vite**.

## Features

### Backend
- JWT authentication (register, login, logout, refresh, forgot/reset password, email verification)
- Organizations with RBAC (8 default roles, permission-code based)
- Teams, Projects, Tasks, Subtasks, Kanban
- Comments, File attachments, Notifications
- Calendar events, Reports & analytics, Activity logs, Global search
- Alembic migrations, OpenAPI spec, Docker Compose

### Frontend
- React + JavaScript + Vite SPA
- Authentication flows with protected routes
- Dashboard with charts (Recharts)
- Projects, Tasks, Kanban (drag-and-drop), Teams, Calendar
- Reports, Notifications, Activity, Users, Settings, Global search
- Responsive dark-theme SaaS layout

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or use Docker)

### Backend

```bash
cp .env.example .env
pip install -r requirements.txt
flask --app backend.run:app db upgrade
python backend/run.py
```

API: `http://localhost:5000/api/v1`  
Health: `GET /api/v1/health`  
OpenAPI: `GET /api/v1/openapi.yaml`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173` (proxies `/api` to backend)

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

## Testing

```bash
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | — |
| `JWT_SECRET_KEY` | JWT signing key (32+ bytes recommended) | — |
| `DATABASE_URL` | PostgreSQL connection string | — |
| `TEST_DATABASE_URL` | Test database (SQLite in-memory) | `sqlite:///:memory:` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `JWT_ACCESS_TOKEN_EXPIRES` | Access token TTL (seconds) | `3600` |
| `VITE_API_URL` | Frontend API base URL | `/api/v1` |

## Project Structure

```
PMS/
├── backend/app/          # Flask application
│   ├── api/              # REST blueprints
│   ├── models/           # SQLAlchemy models
│   ├── repositories/     # Data access layer
│   ├── services/         # Business logic
│   └── utils/            # Helpers, RBAC, responses
├── frontend/src/         # React SPA
│   ├── pages/            # Route pages
│   ├── layouts/          # App shell
│   ├── services/         # API client
│   └── context/          # Auth context
├── migrations/           # Alembic migrations
├── tests/                # Backend pytest suite
├── docker/               # Dockerfiles
└── docs/                 # Architecture & OpenAPI
```

## Architecture

- **Repository + Service** pattern for backend logic
- **UUID** primary keys throughout
- **JWT** bearer authentication with refresh tokens
- **RBAC** enforced at service layer via permission codes
- **Real-time**: abstraction in `realtime_service.py` (WebSocket-ready; polling fallback in frontend)

## API Documentation

Import `docs/openapi.yaml` into Swagger Editor, Postman, or Insomnia.  
Live spec: `GET /api/v1/openapi.yaml`

## License

Private / internal use.
