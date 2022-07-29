from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import (
    DecryptionService,
    ElectionService,
)
from electionguard_gui.services.plaintext_ballot_service import (
    get_plaintext_ballot_report,
)


class ViewTallyComponent(ComponentBase):
    """Responsible for functionality related to viewing a tally"""

    _decryption_service: DecryptionService
    _election_service: ElectionService

    def __init__(
        self, decryption_service: DecryptionService, election_service: ElectionService
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_tally)

    def get_tally(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            self._log.debug(f"retrieving decryption '{decryption_id}'")
            decryption = self._decryption_service.get(db, decryption_id)
            election = self._election_service.get(db, decryption.election_id)
            plaintext_tally = decryption.get_plaintext_tally()
            tally_report = get_plaintext_ballot_report(election, plaintext_tally)
            result = {
                "election_id": election.id,
                "election_name": election.election_name,
                "decryption_name": decryption.decryption_name,
                "report": tally_report,
            }
            return eel_success(result)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)
