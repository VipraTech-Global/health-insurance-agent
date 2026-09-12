from typing import Any, cast


def add_native_view_contracts(
    result: dict[str, Any], generator: Any, request: Any, public: bool
) -> dict[str, Any]:
    del generator, request, public
    paths = cast(dict[str, Any], result.setdefault("paths", {}))
    json_response = {
        "200": {
            "description": "Successful response",
            "content": {"application/json": {"schema": {"type": "object"}}},
        }
    }
    mutation_request = {
        "content": {"application/json": {"schema": {"type": "object"}}},
        "required": True,
    }
    auth_contracts: dict[str, dict[str, tuple[str, dict[str, Any] | None]]] = {
        "/api/v1/auth/csrf/": {"get": ("csrf_state", None)},
        "/api/v1/auth/register/": {"post": ("auth_register", mutation_request)},
        "/api/v1/auth/login/": {"post": ("auth_login", mutation_request)},
        "/api/v1/auth/logout/": {"post": ("auth_logout", None)},
        "/api/v1/auth/session/": {"get": ("auth_session", None)},
        "/api/v1/auth/password/": {"post": ("auth_password_change", mutation_request)},
        "/api/v1/account/": {"delete": ("account_delete", None)},
    }
    for route, operations in auth_contracts.items():
        paths[route] = {}
        for method, (operation_id, request_body) in operations.items():
            operation: dict[str, Any] = {
                "operationId": operation_id,
                "tags": ["auth"],
                "responses": json_response,
            }
            if request_body:
                operation["requestBody"] = request_body
            paths[route][method] = operation

    paths["/api/v1/conversations/{conversation_id}/turns/"] = {
        "get": {
            "operationId": "conversation_turn_list",
            "tags": ["turns"],
            "parameters": [
                {
                    "name": "conversation_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
            ],
            "responses": json_response,
        },
        "post": {
            "operationId": "conversation_turn_stream",
            "tags": ["turns"],
            "parameters": [
                {
                    "name": "conversation_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "format": "uuid"},
                }
            ],
            "requestBody": mutation_request,
            "responses": {
                "200": {
                    "description": "SSE stream of accepted, progress, and one terminal event",
                    "content": {
                        "text/event-stream": {
                            "schema": {"type": "string"},
                        }
                    },
                }
            },
        },
    }
    return result
