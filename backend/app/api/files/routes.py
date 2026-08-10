from flask import Blueprint, request, send_file
from flask_jwt_extended import get_jwt_identity, jwt_required
from io import BytesIO

from backend.app.services.file_service import FileService
from backend.app.utils.responses import build_response

bp = Blueprint("files", __name__, url_prefix="/api/v1/files")
service = FileService()


@bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    user_id = get_jwt_identity()
    if "file" not in request.files:
        return build_response(False, {}, "No file provided", {}, 400)
    file = request.files["file"]
    if not file.filename:
        return build_response(False, {}, "No file selected", {}, 400)
    try:
        result = service.upload(
            user_id,
            file.read(),
            file.filename,
            task_id=request.form.get("task_id"),
            project_id=request.form.get("project_id"),
        )
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, "File uploaded.", {}, 201)


@bp.route("", methods=["GET"])
@jwt_required()
def list_files():
    user_id = get_jwt_identity()
    try:
        result = service.list_files(user_id, request.args.get("task_id"), request.args.get("project_id"))
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 400)
    return build_response(True, result, None, {}, 200)


@bp.route("/<file_id>/download", methods=["GET"])
@jwt_required()
def download_file(file_id):
    user_id = get_jwt_identity()
    try:
        data, mime_type, filename = service.download(user_id, file_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return send_file(BytesIO(data), mimetype=mime_type, as_attachment=True, download_name=filename)


@bp.route("/<file_id>", methods=["DELETE"])
@jwt_required()
def delete_file(file_id):
    user_id = get_jwt_identity()
    try:
        result = service.delete_file(user_id, file_id)
    except PermissionError as exc:
        return build_response(False, {}, str(exc), {}, 403)
    except ValueError as exc:
        return build_response(False, {}, str(exc), {}, 404)
    return build_response(True, result, result.get("message"), {}, 200)
