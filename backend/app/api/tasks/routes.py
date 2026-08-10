from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from backend.app.services.task_service import TaskService
from backend.app.utils.responses import build_response

bp = Blueprint("tasks", __name__, url_prefix="/api/v1/tasks")
service = TaskService()


@bp.route("", methods=["POST"])
@jwt_required()
def create_task():
    user_id = get_jwt_identity()
    try:
        result = service.create_task(user_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Task created.", {}, 201)


@bp.route("", methods=["GET"])
@jwt_required()
def list_tasks():
    user_id = get_jwt_identity()
    try:
        result = service.list_tasks(user_id, request.args.to_dict())
    except (PermissionError, ValueError) as exc:
        code = 403 if isinstance(exc, PermissionError) else 400
        return build_response(False, {}, str(exc), {}, code)
    return build_response(True, result["items"], None, {"pagination": result["pagination"]}, 200)


@bp.route("/<task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_task(user_id, task_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, None, {}, 200)


@bp.route("/<task_id>", methods=["PATCH"])
@jwt_required()
def update_task(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.update_task(user_id, task_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Task updated.", {}, 200)


@bp.route("/<task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_task(user_id, task_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, result.get("message"), {}, 200)


@bp.route("/<task_id>/assign", methods=["POST"])
@jwt_required()
def assign_task(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.assign_task(user_id, task_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Task assigned.", {}, 200)


@bp.route("/<task_id>/subtasks", methods=["POST"])
@jwt_required()
def create_subtask(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.create_subtask(user_id, task_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Subtask created.", {}, 201)


@bp.route("/<task_id>/subtasks/<subtask_id>", methods=["PATCH"])
@jwt_required()
def update_subtask(task_id, subtask_id):
    user_id = get_jwt_identity()
    try:
        result = service.update_subtask(user_id, task_id, subtask_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Subtask updated.", {}, 200)


@bp.route("/<task_id>/subtasks/<subtask_id>", methods=["DELETE"])
@jwt_required()
def delete_subtask(task_id, subtask_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_subtask(user_id, task_id, subtask_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, result.get("message"), {}, 200)


@bp.route("/kanban/<project_id>", methods=["GET"])
@jwt_required()
def kanban_board(project_id):
    user_id = get_jwt_identity()
    try:
        result = service.get_kanban_board(user_id, project_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result, None, {}, 200)


@bp.route("/<task_id>/move", methods=["POST"])
@jwt_required()
def move_task(task_id):
    user_id = get_jwt_identity()
    try:
        result = service.move_task(user_id, task_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "Task moved.", {}, 200)


@bp.route("/kanban/<project_id>/reorder", methods=["POST"])
@jwt_required()
def bulk_reorder(project_id):
    user_id = get_jwt_identity()
    try:
        result = service.bulk_reorder(user_id, project_id, request.get_json(silent=True) or {})
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    return build_response(True, result, "Board reordered.", {}, 200)
