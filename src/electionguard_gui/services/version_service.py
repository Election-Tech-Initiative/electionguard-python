from os import path
from typing import Optional
import eel
from git import Repo
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
        repo = Repo("./")
        commit_hash = repo.git.rev_parse("HEAD")
        short_hash = str(commit_hash[:6])
        self._log.info(f"Version: {short_hash}")
        return short_hash
