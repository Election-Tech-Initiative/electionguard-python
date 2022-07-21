from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase


class CreateElectionComponent(ComponentBase):
    """Responsible for functionality related to creating encryption packages for elections"""

    def expose(self) -> None:
        eel.expose(self.get_keys)

    def get_keys(self) -> dict[str, Any]:
        return eel_success(["Key 1", "Key 2", "Key 3", "Key 4"])
