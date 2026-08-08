# System Architecture Overview

```mermaid
flowchart LR
    Browser[Browser / Bootstrap UI] --> Nginx[Nginx Reverse Proxy]
    Nginx --> Flask[Flask Application]
    Flask --> ORM[SQLAlchemy ORM]
    ORM --> Postgres[(PostgreSQL)]
    Flask --> Redis[(Redis)]
    Flask --> SocketIO[Flask-SocketIO]
    SocketIO --> Browser
    Flask --> Celery[Celery Workers]
    Celery --> Postgres
    Celery --> Redis
```

## Architectural Notes
- The Flask application will expose REST endpoints for core project management workflows.
- WebSocket channels will support real-time notifications, chat updates, and collaborative task events.
- Celery workers will handle report generation, email notifications, and asynchronous processing.
- PostgreSQL remains the source of truth for transactional state.
- Redis supports caching, session handling, and task queue management.
