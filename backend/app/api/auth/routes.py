from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from backend.app.services.auth_service import AuthService
from backend.app.utils.responses import build_response

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")
service = AuthService()


@bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json(silent=True) or {}
    try:
        result = service.register(payload)
    except ValueError as exc:
        if str(exc) == "Email already registered" or str(exc) == "Username already registered":
            return build_response(False, {}, str(exc), {}, 409)
        if str(exc) in {"Invalid email address", "Password must be at least 12 characters long", "Password must contain at least one uppercase letter", "Password must contain at least one lowercase letter", "Password must contain at least one number", "Password must contain at least one special character"}:
            return build_response(False, {}, str(exc), {}, 422)
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Registration successful. Please verify your email.", {}, 201)


@bp.route("/login", methods=["POST"])
def login():
    payload = request.get_json(silent=True) or {}
    try:
        result = service.login(payload)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 401)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result, "Login successful.", {}, 200)


@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    identity = get_jwt_identity()
    service.logout(identity)
    return build_response(True, {}, "Logout successful.", {}, 200)


@bp.route("/refresh", methods=["POST"])
def refresh():
    payload = request.get_json(silent=True) or {}
    try:
        result = service.refresh(payload.get("refresh_token", ""))
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 401)
    return build_response(True, result, None, {}, 200)


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    if not email:
        return build_response(False, {}, "Email is required", {}, 422)
    result = service.forgot_password(email)
    return build_response(True, {}, "If an account exists, a reset link has been sent.", {"reset_token": result.get("reset_token")}, 200)


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")
    new_password = payload.get("new_password")
    if not token or not new_password:
        return build_response(False, {}, "Token and new password are required", {}, 422)
    try:
        result = service.reset_password(token, new_password)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 422)
    return build_response(True, {}, result["message"], {}, 200)


@bp.route("/verify-email", methods=["POST"])
def verify_email():
    payload = request.get_json(silent=True) or {}
    token = payload.get("token")
    if not token:
        return build_response(False, {}, "Token is required", {}, 422)
    try:
        result = service.verify_email(token)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 422)
    return build_response(True, {}, result["message"], {}, 200)
