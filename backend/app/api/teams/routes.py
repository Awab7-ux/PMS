from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.organization_service import OrganizationService
from backend.app.utils.responses import build_response

bp = Blueprint("teams", __name__, url_prefix="/api/v1/teams")
service = OrganizationService()


@bp.route("", methods=["POST"])
@jwt_required()
def create_team():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.create_team(user_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Team created successfully.", {}, 201)


@bp.route("", methods=["GET"])
@jwt_required()
def list_teams():
    user_id = get_jwt_identity()
    result = service.list_teams(user_id)
    return build_response(True, result, "Teams retrieved successfully.", {}, 200)


@bp.route("/<team_id>", methods=["GET"])
@jwt_required()
def get_team(team_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_team(user_id, team_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Team retrieved successfully.", {}, 200)


@bp.route("/<team_id>", methods=["PATCH"])
@jwt_required()
def update_team(team_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.update_team(user_id, team_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Team updated successfully.", {}, 200)


@bp.route("/<team_id>", methods=["DELETE"])
@jwt_required()
def delete_team(team_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_team(user_id, team_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Team archived successfully.", {}, 200)


@bp.route("/<team_id>/members", methods=["POST"])
@jwt_required()
def add_team_member(team_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.add_team_member(user_id, team_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Team member added successfully.", {}, 201)


@bp.route("/<team_id>/members", methods=["GET"])
@jwt_required()
def list_team_members(team_id):
    user_id = get_jwt_identity()
    try:
        result = service.list_team_members(user_id, team_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Team members retrieved successfully.", {}, 200)


@bp.route("/<team_id>/members/<user_id>", methods=["DELETE"])
@jwt_required()
def remove_team_member(team_id, user_id):
    acting_user_id = get_jwt_identity()
    try:
        result = service.remove_team_member(acting_user_id, team_id, user_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Team member removed successfully.", {}, 200)
