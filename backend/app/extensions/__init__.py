from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


def init_extensions(app: Flask, db: SQLAlchemy, migrate: Migrate, jwt: JWTManager) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
