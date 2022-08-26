from os import path
from subprocess import check_output
from typing import Optional
import eel
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class VersionService(ServiceBase):
    """Responsible for retrieving version information"""

    _log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self._log = log_service

    def expose(self) -> None:
        eel.expose(self.get_version)

    def get_version(self) -> Optional[str]:
        if not path.exists(".git"):
            return None
        commit_hash = (
            check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("ascii")
            .strip()
        )
        self._log.info(f"Version: {commit_hash}")
        return commit_hash
