from typing import Any
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.services import ElectionService


class UploadBallotsComponent(ComponentBase):
    """Responsible for uploading ballots to an election via the GUI"""

    _election_service: ElectionService

    def __init__(self, election_service: ElectionService) -> None:
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.upload_ballots)

    def upload_ballots(self, election_id: str) -> dict[str, Any]:
        db = self._db_service.get_db()
        self._log.debug(f"uploading ballots to {election_id}")
        election = self._election_service.get(db, election_id)
        return eel_success(election.to_dict())
