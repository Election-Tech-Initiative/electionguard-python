from abc import ABC
from typing import Any

from electionguard_gui.services.db_service import DbService


class ComponentBase(ABC):
    """Responsible for common functionality among ell components"""

    db_service: DbService

    def eel_fail(self, message: str) -> dict[str, Any]:
        return {"success": False, "message": message}

    def eel_success(self, result: Any = None) -> dict[str, Any]:
        return {"success": True, "result": str(result)}

    def init(self, db_service: DbService) -> None:
        self.db_service = db_service
        self.expose()

    def expose(self) -> None:
        pass
