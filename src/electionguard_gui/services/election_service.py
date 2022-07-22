from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class ElectionService(ServiceBase):
    """Responsible for functionality related to elections"""

    _log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self._log = log_service
