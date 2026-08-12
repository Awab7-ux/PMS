from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.organization_service import OrganizationService
from backend.app.utils.responses import build_response

bp = Blueprint("organizations", __name__, url_prefix="/api/v1/organizations")
service = OrganizationService()


@bp.route("", methods=["POST"])
@jwt_required()
def create_organization():
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.create_organization(user_id, payload)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Organization created successfully.", {}, 201)


@bp.route("", methods=["GET"])
@jwt_required()
def list_organizations():
    user_id = get_jwt_identity()
    result = service.list_organizations(user_id)
    return build_response(True, result, "Organizations retrieved successfully.", {}, 200)


@bp.route("/<organization_id>", methods=["GET"])
@jwt_required()
def get_organization(organization_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_organization(user_id, organization_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Organization retrieved successfully.", {}, 200)


@bp.route("/<organization_id>", methods=["PATCH"])
@jwt_required()
def update_organization(organization_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.update_organization(user_id, organization_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Organization updated successfully.", {}, 200)


@bp.route("/<organization_id>", methods=["DELETE"])
@jwt_required()
def delete_organization(organization_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_organization(user_id, organization_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, "Organization archived successfully.", {}, 200)


@bp.route("/<organization_id>/members", methods=["GET"])
@jwt_required()
def list_members(organization_id):
    user_id = get_jwt_identity()
    try:
        result = service.list_members(user_id, organization_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result, "Members retrieved successfully.", {}, 200)


@bp.route("/<organization_id>/members", methods=["POST"])
@jwt_required()
def add_member(organization_id):
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.add_member(user_id, organization_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Member added successfully.", {}, 201)


@bp.route("/<organization_id>/members/<user_id>", methods=["PATCH"])
@jwt_required()
def update_member(organization_id, user_id):
    acting_user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    try:
        result = service.update_member(acting_user_id, organization_id, user_id, payload)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Member updated successfully.", {}, 200)


@bp.route("/<organization_id>/members/<user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(organization_id, user_id):
    acting_user_id = get_jwt_identity()
    try:
        result = service.remove_member(acting_user_id, organization_id, user_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Member removed successfully.", {}, 200)
