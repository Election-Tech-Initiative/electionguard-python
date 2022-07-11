from abc import ABC

from electionguard_gui.services.db_service import DbService


class ComponentBase(ABC):
    """Responsible for common functionality among ell components"""

    db_service: DbService

    def init(self, db_service: DbService) -> None:
        self.db_service = db_service
        self.expose()

    def expose(self) -> None:
        pass
