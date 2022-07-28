from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import ElectionService, DecryptionService


class ExportElectionRecordComponent(ComponentBase):
    """Responsible for exporting an election record for an election"""

    _election_service: ElectionService
    _decryption_service: DecryptionService

    def __init__(
        self, election_service: ElectionService, decryption_service: DecryptionService
    ) -> None:
        self._election_service = election_service
        self._decryption_service = decryption_service

    def expose(self) -> None:
        eel.expose(self.export_election_record)

    def export_election_record(
        self, decryption_id: str, location: str
    ) -> dict[str, Any]:
        db = self._db_service.get_db()
        self._log.debug(f"exporting election record {decryption_id} to {location}")
        # election = self._election_service.get(db, election_id)

        return eel_success()
