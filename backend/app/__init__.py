import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from backend.app.config import get_config
from backend.app.extensions import init_extensions


db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    init_extensions(app, db=db, migrate=migrate, jwt=jwt)

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    from backend.app.api.auth.routes import bp as auth_bp
    from backend.app.api.users.routes import bp as users_bp
    from backend.app.api.organizations.routes import bp as organizations_bp
    from backend.app.api.teams.routes import bp as teams_bp
    from backend.app.api.projects.routes import bp as projects_bp
    from backend.app.api.tasks.routes import bp as tasks_bp
    from backend.app.api.comments.routes import bp as comments_bp
    from backend.app.api.files.routes import bp as files_bp
    from backend.app.api.notifications.routes import bp as notifications_bp
    from backend.app.api.misc.routes import (
        calendar_bp,
        reports_bp,
        search_bp,
        activity_bp,
    )

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(organizations_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(activity_bp)

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found", "message": "The requested resource was not found."}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

    @app.route("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "service": "pms-backend"})

    return app
