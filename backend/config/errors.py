from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None
    message = "Request failed."
    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            message = str(detail)
    response.data = {
        "error": {
            "code": getattr(exc, "default_code", "request_error"),
            "message": message,
            "details": response.data,
        }
    }
    return response
