import logging
import os
import sys
from logging.config import fileConfig

from alembic import context
from flask import current_app

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("script_location", os.path.abspath(os.path.dirname(__file__)))

from backend.app import db
from backend.app.models import User, Organization, Team, Project

target_metadata = db.metadata


def run_migrations_offline() -> None:
    url = current_app.config.get("SQLALCHEMY_DATABASE_URI")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with current_app.app_context():
        configuration = config.get_section(config.config_ini_section)
        configuration["sqlalchemy.url"] = current_app.config.get("SQLALCHEMY_DATABASE_URI")
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
