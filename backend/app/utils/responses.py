from flask import jsonify


def build_response(success: bool, data=None, message=None, meta=None, status_code=200, errors=None):
    body = {
        "success": success,
        "data": data if data is not None else {},
        "message": message,
        "meta": meta or {},
    }
    if errors is not None:
        body["errors"] = errors
    return jsonify(body), status_code
