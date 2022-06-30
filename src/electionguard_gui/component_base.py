from abc import ABC
from typing import Any
from pymongo import MongoClient
from pymongo.database import Database


class ComponentBase(ABC):
    """Responsible for common functionality among ell components"""

    def get_db(self) -> Database:
        # todo: parameterize db credentials here and in docker-compose.db.yml
        client: MongoClient = MongoClient(
            "localhost", 27017, username="root", password="example"
        )
        db: Database = client.ElectionGuardDb
        return db

    def eel_fail(self, message: str) -> dict[str, Any]:
        return {"success": False, "message": message}

    def eel_success(self, result: Any = None) -> dict[str, Any]:
        return {"success": True, "result": result}

    def expose(self) -> None:
        pass
