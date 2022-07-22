from typing import Any
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.services import ElectionService


class ViewElectionComponent(ComponentBase):
    """Responsible for viewing election details"""

    _election_service: ElectionService

    def __init__(self, election_service: ElectionService) -> None:
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_election)
        eel.expose(self.download_election_package)

    def get_election(self, election_id: str) -> dict[str, Any]:
        db = self._db_service.get_db()
        election = self._election_service.get(db, election_id)
        return eel_success(election.to_dict())

    def download_election_package(self, election_id: str) -> dict[str, Any]:
        db = self._db_service.get_db()
        election = self._election_service.get(db, election_id)
        self._log.debug(f"found encryption package: {election.encryption_package_file}")
        return eel_success(election.encryption_package_file)
