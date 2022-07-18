from abc import ABC

from electionguard_gui.services.db_service import DbService
from electionguard_gui.services.eel_log_service import EelLogService


class ComponentBase(ABC):
    """Responsible for common functionality among ell components"""

    db_service: DbService
    log: EelLogService

    def init(
        self,
        db_service: DbService,
        log_service: EelLogService,
    ) -> None:
        self.db_service = db_service
        self.log = log_service
        self.expose()

    def expose(self) -> None:
        """Override to expose the component's methods to JavaScript. This technique hides the
        fact that method names exposed must be globally unique."""
