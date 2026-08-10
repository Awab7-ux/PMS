from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.calendar_service import CalendarService
from backend.app.services.report_service import ReportService
from backend.app.services.search_service import SearchService
from backend.app.utils.responses import build_response

calendar_bp = Blueprint("calendar", __name__, url_prefix="/api/v1/calendar")
reports_bp = Blueprint("reports", __name__, url_prefix="/api/v1/reports")
search_bp = Blueprint("search", __name__, url_prefix="/api/v1/search")
activity_bp = Blueprint("activity", __name__, url_prefix="/api/v1/activity")

calendar_service = CalendarService()
report_service = ReportService()
search_service = SearchService()


@calendar_bp.route("/events", methods=["GET"])
@jwt_required()
def get_events():
    user_id = get_jwt_identity()
    try:
        result = calendar_service.get_events(user_id, request.args.to_dict())
    except (PermissionError, ValueError) as exc:
        code = 403 if isinstance(exc, PermissionError) else 400
        return build_response(False, {}, str(exc), {}, code)
    return build_response(True, result, None, {}, 200)


@reports_bp.route("/analytics", methods=["GET"])
@jwt_required()
def analytics():
    user_id = get_jwt_identity()
    org_id = request.args.get("organization_id")
    if not org_id:
        return build_response(False, {}, "organization_id is required", {}, 400)
    try:
        result = report_service.get_analytics(user_id, org_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result, None, {}, 200)


@search_bp.route("", methods=["GET"])
@jwt_required()
def global_search():
    user_id = get_jwt_identity()
    try:
        result = search_service.global_search(user_id, request.args.to_dict())
    except (PermissionError, ValueError) as exc:
        code = 403 if isinstance(exc, PermissionError) else 400
        return build_response(False, {}, str(exc), {}, code)
    return build_response(True, result, None, {}, 200)


@activity_bp.route("", methods=["GET"])
@jwt_required()
def list_activity():
    user_id = get_jwt_identity()
    try:
        result = report_service.get_activity(user_id, request.args.to_dict())
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result["items"], None, {"pagination": result["pagination"]}, 200)
