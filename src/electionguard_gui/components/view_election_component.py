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

    def get_election(self, election_id: str) -> dict[str, Any]:
        db = self._db_service.get_db()
        election = self._election_service.get(db, election_id)
        return eel_success(election.to_dict())
