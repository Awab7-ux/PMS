from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.event_service import EventService
from backend.app.utils.responses import build_response

bp = Blueprint("events", __name__, url_prefix="/api/v1/events")
service = EventService()

def invoke(callback, *args):
    try: return build_response(True, callback(*args), None, {}, 200)
    except PermissionError as exc: return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc: return build_response(False, {}, str(exc), {}, 400)

@bp.route("", methods=["POST"])
@jwt_required()
def create_event():
    try:
        result = service.create(get_jwt_identity(), request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Event created", {}, 201)

@bp.route("", methods=["GET"])
@jwt_required()
def list_events(): return invoke(service.list, get_jwt_identity(), request.args.to_dict())

@bp.route("/<event_id>", methods=["GET"])
@jwt_required()
def get_event(event_id): return invoke(service.get, get_jwt_identity(), event_id)

@bp.route("/<event_id>", methods=["PATCH"])
@jwt_required()
def update_event(event_id): return invoke(service.update, get_jwt_identity(), event_id, request.get_json(silent=True) or {})

@bp.route("/<event_id>", methods=["DELETE"])
@jwt_required()
def delete_event(event_id): return invoke(service.delete, get_jwt_identity(), event_id)
