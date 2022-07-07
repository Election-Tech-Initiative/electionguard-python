from typing import Any


def eel_fail(message: str) -> dict[str, Any]:
    return {"success": False, "message": message}


def eel_success(result: Any = None) -> dict[str, Any]:
    return {"success": True, "result": str(result)}
