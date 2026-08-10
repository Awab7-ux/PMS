from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.support_services import NotificationService
from backend.app.utils.responses import build_response

bp = Blueprint("notifications", __name__, url_prefix="/api/v1/notifications")
service = NotificationService()


@bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    result = service.list_notifications(user_id, request.args.to_dict())
    return build_response(True, result["items"], None, {"pagination": result["pagination"], "unread_count": result["unread_count"]}, 200)


@bp.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    user_id = get_jwt_identity()
    from backend.app.repositories.support_repositories import NotificationRepository
    count = NotificationRepository().count_unread(user_id)
    return build_response(True, {"count": count}, None, {}, 200)


@bp.route("/<notification_id>/read", methods=["POST"])
@jwt_required()
def mark_read(notification_id):
    user_id = get_jwt_identity()
    try:
        result = service.mark_read(user_id, notification_id)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Marked as read.", {}, 200)


@bp.route("/read-all", methods=["POST"])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    result = service.mark_all_read(user_id)
    return build_response(True, result, result.get("message"), {}, 200)


@bp.route("/<notification_id>", methods=["DELETE"])
@jwt_required()
def delete_notification(notification_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_notification(user_id, notification_id)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, result.get("message"), {}, 200)
