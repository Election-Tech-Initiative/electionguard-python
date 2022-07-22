from typing import Any
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.services import ElectionService


class ElectionListComponent(ComponentBase):
    """Responsible for displaying multiple elections"""

    _election_service: ElectionService

    def __init__(self, election_service: ElectionService) -> None:
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_elections)

    def get_elections(self) -> dict[str, Any]:
        db = self._db_service.get_db()
        elections = self._election_service.get_all(db)
        elections_list = [election.to_id_name_dict() for election in elections]
        return eel_success(elections_list)
