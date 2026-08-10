from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.support_services import CommentService, NotificationService
from backend.app.utils.responses import build_response

bp = Blueprint("comments", __name__, url_prefix="/api/v1")
service = CommentService()


@bp.route("/tasks/<task_id>/comments", methods=["GET"])
@jwt_required()
def list_comments(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.list_comments(user_id, task_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, None, {}, 200)


@bp.route("/tasks/<task_id>/comments", methods=["POST"])
@jwt_required()
def create_comment(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.create_comment(user_id, task_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Comment added.", {}, 201)


@bp.route("/comments/<comment_id>", methods=["PATCH"])
@jwt_required()
def update_comment(comment_id):
    user_id = get_jwt_identity()
    try:
        result = service.update_comment(user_id, comment_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Comment updated.", {}, 200)


@bp.route("/comments/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_comment(user_id, comment_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, result.get("message"), {}, 200)
