from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import ElectionService


class ExportEncryptionPackage(ComponentBase):
    """Responsible for exporting an encryption package for an election"""

    _election_service: ElectionService

    def __init__(self, election_service: ElectionService) -> None:
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_export_locations)
        eel.expose(self.export)

    def get_export_locations(self) -> dict[str, Any]:
        return eel_success(["d:\\temp", "e:\\"])

    def export(self, election_id: str) -> dict[str, Any]:
        return eel_success("exported")
