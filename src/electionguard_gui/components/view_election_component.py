from typing import Any
import eel
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.eel_utils import eel_success


class ViewElectionComponent(ComponentBase):
    """Responsible for viewing election details"""

    def expose(self) -> None:
        eel.expose(self.get_election)

    def get_election(self, election_id: str) -> dict[str, Any]:
        return eel_success({"election_name": "Fred"})
