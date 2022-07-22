from typing import Any
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success


class ElectionListComponent(ComponentBase):
    """Responsible for displaying multiple elections"""

    def expose(self) -> None:
        eel.expose(self.get_elections)

    def get_elections(self) -> dict[str, Any]:
        db = self._db_service.get_db()
        elections = db.elections.find()
        elections_list = [
            {"id": str(election["_id"]), "election_name": election["election_name"]}
            for election in elections
        ]
        return eel_success(elections_list)
