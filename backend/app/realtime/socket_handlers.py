from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import disconnect, emit, join_room, leave_room

from backend.app.repositories.organization_repository import OrganizationRepository, TeamRepository
from backend.app.repositories.task_repository import TaskRepository
from backend.app.services.rbac_service import RBACService


def register_socket_handlers(socketio):
    """Register once; every client-supplied room is authorized server-side."""
    sid_users: dict[str, str] = {}

    def identity_from_auth(auth):
        token = (auth or {}).get("token")
        if not token:
            return None
        try:
            return str(decode_token(token)["sub"])
        except Exception:
            return None

    def authorize(user_id, room_type, resource_id):
        rbac = RBACService()
        if room_type == "organization":
            rbac.require_org_membership(user_id, resource_id)
            return
        if room_type == "project":
            rbac.require_project_access(user_id, resource_id)
            return
        if room_type == "task":
            task = TaskRepository().get_by_id(resource_id)
            if not task:
                raise ValueError("Task not found")
            rbac.require_project_access(user_id, str(task.project_id))
            return
        if room_type == "team":
            team = TeamRepository().get_by_id(resource_id)
            if not team or not team.is_active:
                raise ValueError("Team not found")
            membership = OrganizationRepository().get_membership(team.organization_id, user_id)
            team_membership = TeamRepository().get_membership(team.id, user_id)
            if not membership or membership.status != "active" or (not team_membership and membership.role.name not in {"Organization Owner", "Project Manager"}):
                raise PermissionError("Access denied")
            return
        raise ValueError("Unsupported room type")

    @socketio.on("connect")
    def connect(auth):
        user_id = identity_from_auth(auth)
        if not user_id:
            return False
        sid_users[request.sid] = user_id
        emit("presence.changed", {"user_id": user_id, "status": "online"}, to=request.sid)

    @socketio.on("disconnect")
    def on_disconnect():
        sid_users.pop(request.sid, None)

    @socketio.on("room.join")
    def join(data):
        user_id = sid_users.get(request.sid)
        room_type, resource_id = (data or {}).get("type"), (data or {}).get("id")
        if not user_id or not room_type or not resource_id:
            emit("room.error", {"message": "Authentication and room details are required"})
            return
        try:
            authorize(user_id, room_type, resource_id)
        except (PermissionError, ValueError):
            emit("room.error", {"message": "Access denied"})
            return
        room = f"{room_type}:{resource_id}"
        join_room(room)
        emit("room.joined", {"room": room})

    @socketio.on("room.leave")
    def leave(data):
        room_type, resource_id = (data or {}).get("type"), (data or {}).get("id")
        if room_type and resource_id:
            leave_room(f"{room_type}:{resource_id}")
