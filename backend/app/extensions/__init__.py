from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO


def init_extensions(app: Flask, db: SQLAlchemy, migrate: Migrate, jwt: JWTManager, socketio: SocketIO | None = None) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    if socketio:
        socketio.init_app(app, cors_allowed_origins=app.config.get("CORS_ORIGINS", "*"), async_mode="threading")
