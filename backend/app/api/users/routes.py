from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.user_service import UserService
from backend.app.utils.responses import build_response

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")
service = UserService()
auth_service_user = __import__("backend.app.services.auth_service", fromlist=["AuthService"]).AuthService()


@bp.route("/me", methods=["GET"])
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    try:
        user = auth_service_user.get_current_user(user_id)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, user, None, {}, 200)


@bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.update_profile(user_id, payload)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Profile updated.", {}, 200)


@bp.route("/me/password", methods=["PATCH"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.change_password(user_id, payload)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 422)
    return build_response(True, result, result.get("message"), {}, 200)


@bp.route("", methods=["GET"])
@jwt_required()
def list_users():
    user_id = get_jwt_identity()
    try:
        result = service.list_users(user_id, request.args.get("organization_id"), request.args.get("search"), int(request.args.get("page") or 1), int(request.args.get("per_page") or 20))
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result["items"], None, {"pagination": result["pagination"]}, 200)


@bp.route("/<target_user_id>", methods=["GET"])
@jwt_required()
def get_user(target_user_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_user(user_id, target_user_id, request.args.get("organization_id"))
    except (PermissionError, ValueError) as exc:
        code = 403 if isinstance(exc, PermissionError) else 404
        return build_response(False, {}, str(exc), {}, code)
    return build_response(True, result, None, {}, 200)
