from datetime import timezone, datetime
from typing import Any


def eel_fail(message: str) -> dict[str, Any]:
    return {"success": False, "message": message}


def eel_success(result: Any = None) -> dict[str, Any]:
    return {"success": True, "result": result}


def utc_to_str(utc_dt: datetime) -> str:
    local = convert_utc_to_local(utc_dt)
    return local.strftime("%b %#d, %Y %#I:%M %p")


def convert_utc_to_local(utc_dt: datetime) -> datetime:
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(None)
