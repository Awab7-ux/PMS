from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.auth_service import AuthService

bp = Blueprint("users", __name__, url_prefix="/api/v1/users")
service = AuthService()


def build_response(success: bool, data=None, message=None, meta=None, status_code=200):
    return jsonify({
        "success": success,
        "data": data or {},
        "message": message,
        "meta": meta or {},
    }), status_code


@bp.route("/me", methods=["GET"])
@jwt_required()
def current_user():
    user_id = get_jwt_identity()
    try:
        user = service.get_current_user(user_id)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, user, None, {}, 200)
