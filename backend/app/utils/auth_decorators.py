import uuid
from functools import wraps
from typing import Callable

from flask import g
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.rbac_service import RBACService


def require_permission(permission_code: str, organization_id_param: str | None = None):
    """Decorator to enforce permission codes on API routes."""

    def decorator(fn: Callable):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            org_id = kwargs.get(organization_id_param) if organization_id_param else None
            if not org_id:
                org_id = kwargs.get("project_id") or kwargs.get("team_id")
            rbac = RBACService()
            if not rbac.has_permission(user_id, permission_code, organization_id=org_id, context=kwargs):
                from backend.app.utils.responses import build_response
                return build_response(False, {}, "Insufficient permissions", {}, 403)
            g.current_user_id = user_id
            return fn(*args, **kwargs)

        return wrapper

    return decorator
