from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.project_service import ProjectService
from backend.app.utils.responses import build_response

bp = Blueprint("projects", __name__, url_prefix="/api/v1/projects")
service = ProjectService()


@bp.route("", methods=["POST"])
@jwt_required()
def create_project():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.create_project(user_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Project created successfully.", {}, 201)


@bp.route("", methods=["GET"])
@jwt_required()
def list_projects():
    user_id = get_jwt_identity()
    result = service.list_projects(user_id, request.args.to_dict())
    return build_response(
        True,
        result["items"],
        "Projects retrieved successfully.",
        {"pagination": result["pagination"]},
        200,
    )


@bp.route("/<project_id>", methods=["GET"])
@jwt_required()
def get_project(project_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_project(user_id, project_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Project retrieved successfully.", {}, 200)


@bp.route("/<project_id>", methods=["PATCH"])
@jwt_required()
def update_project(project_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.update_project(user_id, project_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Project updated successfully.", {}, 200)


@bp.route("/<project_id>", methods=["DELETE"])
@jwt_required()
def delete_project(project_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_project(user_id, project_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Project archived successfully.", {}, 200)


@bp.route("/<project_id>/members", methods=["GET"])
@jwt_required()
def list_members(project_id):
    user_id = get_jwt_identity()
    try:
        result = service.list_members(user_id, project_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Members retrieved successfully.", {}, 200)


@bp.route("/<project_id>/members", methods=["POST"])
@jwt_required()
def add_member(project_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.add_member(user_id, project_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Member added successfully.", {}, 201)


@bp.route("/<project_id>/members/<member_user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(project_id, member_user_id):
    acting_user_id = get_jwt_identity()
    try:
        result = service.remove_member(acting_user_id, project_id, member_user_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Member removed successfully.", {}, 200)
