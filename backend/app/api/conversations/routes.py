from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.chat_service import ConversationService
from backend.app.utils.responses import build_response

bp = Blueprint("conversations", __name__, url_prefix="/api/v1/conversations")
service = ConversationService()


@bp.route("", methods=["GET"])
@jwt_required()
def list_conversations():
    """List conversations for the authenticated user."""
    user_id = get_jwt_identity()
    organization_id = request.args.get("organization_id")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    if not organization_id:
        return build_response(False, {}, "organization_id is required", {}, 400)

    try:
        result = service.list_conversations(user_id, organization_id, page, per_page)
        return build_response(True, result["items"], None, {"pagination": result["pagination"]}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>", methods=["GET"])
@jwt_required()
def get_conversation(conversation_id):
    """Get conversation details."""
    user_id = get_jwt_identity()

    try:
        result = service.get_conversation(user_id, conversation_id)
        return build_response(True, result, None, {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/direct", methods=["POST"])
@jwt_required()
def create_direct_message():
    """Create or get a direct message conversation."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    other_user_id = payload.get("other_user_id")
    organization_id = payload.get("organization_id")

    if not other_user_id or not organization_id:
        return build_response(False, {}, "other_user_id and organization_id are required", {}, 400)

    try:
        result = service.create_direct_message_conversation(user_id, other_user_id, organization_id)
        return build_response(True, result, "Conversation created or retrieved", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/group", methods=["POST"])
@jwt_required()
def create_group_conversation():
    """Create a group conversation."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    organization_id = payload.get("organization_id")

    if not organization_id:
        return build_response(False, {}, "organization_id is required", {}, 400)

    try:
        result = service.create_group_conversation(user_id, organization_id, payload)
        return build_response(True, result, "Group conversation created", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/project/<project_id>", methods=["POST"])
@jwt_required()
def create_project_conversation(project_id):
    """Create or get a project conversation."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    organization_id = payload.get("organization_id")

    if not organization_id:
        return build_response(False, {}, "organization_id is required", {}, 400)

    try:
        result = service.create_project_conversation(user_id, organization_id, project_id)
        return build_response(True, result, "Project conversation created or retrieved", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/team/<team_id>", methods=["POST"])
@jwt_required()
def create_team_conversation(team_id):
    """Create or get a team conversation."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    organization_id = payload.get("organization_id")

    if not organization_id:
        return build_response(False, {}, "organization_id is required", {}, 400)

    try:
        result = service.create_team_conversation(user_id, organization_id, team_id)
        return build_response(True, result, "Team conversation created or retrieved", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>", methods=["PATCH"])
@jwt_required()
def update_conversation(conversation_id):
    """Update a conversation (group only)."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    try:
        result = service.update_conversation(user_id, conversation_id, payload)
        return build_response(True, result, "Conversation updated", {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>", methods=["DELETE"])
@jwt_required()
def delete_conversation(conversation_id):
    """Delete a conversation (soft delete)."""
    user_id = get_jwt_identity()

    try:
        result = service.delete_conversation(user_id, conversation_id)
        return build_response(True, {}, result.get("message"), {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


# Conversation members endpoints
@bp.route("/<conversation_id>/members", methods=["GET"])
@jwt_required()
def get_conversation_members(conversation_id):
    """Get members of a conversation."""
    user_id = get_jwt_identity()

    try:
        result = service.get_members(user_id, conversation_id)
        return build_response(True, result["items"], None, {"count": result["count"]}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>/members", methods=["POST"])
@jwt_required()
def add_conversation_member(conversation_id):
    """Add a member to a conversation (group only)."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}
    new_member_id = payload.get("user_id")

    if not new_member_id:
        return build_response(False, {}, "user_id is required", {}, 400)

    try:
        result = service.add_member(user_id, conversation_id, new_member_id)
        return build_response(True, result, "Member added", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>/members/<member_id>", methods=["DELETE"])
@jwt_required()
def remove_conversation_member(conversation_id, member_id):
    """Remove a member from a conversation (group only)."""
    user_id = get_jwt_identity()

    try:
        result = service.remove_member(user_id, conversation_id, member_id)
        return build_response(True, {}, result.get("message"), {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


# Messages endpoints
@bp.route("/<conversation_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(conversation_id):
    """Get messages from a conversation."""
    user_id = get_jwt_identity()
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))

    # Support polling with "after" parameter
    after_message_id = request.args.get("after")

    try:
        if after_message_id:
            result = service.get_messages_after(user_id, conversation_id, after_message_id, limit)
        else:
            result = service.get_messages(user_id, conversation_id, limit, offset)
        return build_response(True, result["items"], None, result.get("pagination") or {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>/messages", methods=["POST"])
@jwt_required()
def send_message(conversation_id):
    """Send a message to a conversation."""
    user_id = get_jwt_identity()
    payload = request.get_json(silent=True) or {}

    try:
        result = service.send_message(user_id, conversation_id, payload)
        return build_response(True, result, "Message sent", {}, 201)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("/<conversation_id>/read", methods=["POST"])
@jwt_required()
def mark_conversation_read(conversation_id):
    """Mark a conversation as read."""
    user_id = get_jwt_identity()

    try:
        result = service.mark_as_read(user_id, conversation_id)
        return build_response(True, result, "Conversation marked as read", {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


# Message operations - Using alternative route pattern
@bp.route("", methods=["PATCH"])
@jwt_required()
def edit_message_alt():
    """Edit a message via query parameter."""
    user_id = get_jwt_identity()
    message_id = request.args.get("message_id")
    payload = request.get_json(silent=True) or {}

    if not message_id:
        return build_response(False, {}, "message_id is required", {}, 400)

    try:
        result = service.edit_message(user_id, message_id, payload)
        return build_response(True, result, "Message updated", {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)


@bp.route("", methods=["DELETE"])
@jwt_required()
def delete_message_alt():
    """Delete a message via query parameter."""
    user_id = get_jwt_identity()
    message_id = request.args.get("message_id")

    if not message_id:
        return build_response(False, {}, "message_id is required", {}, 400)

    try:
        result = service.delete_message(user_id, message_id)
        return build_response(True, {}, result.get("message"), {}, 200)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    except Exception as exc:
        return build_response(False, {}, f"An error occurred: {str(exc)}", {}, 500)
