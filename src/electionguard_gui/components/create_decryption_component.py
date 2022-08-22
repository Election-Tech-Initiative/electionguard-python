from typing import Any
import eel
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.models.election_dto import ElectionDto
from electionguard_gui.services import ElectionService, DecryptionService


class CreateDecryptionComponent(ComponentBase):
    """Responsible for functionality related to creating decryptions for an election"""

    _decryption_service: DecryptionService
    _election_service: ElectionService

    def __init__(
        self,
        decryption_service: DecryptionService,
        election_service: ElectionService,
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.create_decryption)
        eel.expose(self.get_suggested_decryption_name)

    def get_suggested_decryption_name(self, election_id: str) -> dict[str, Any]:
        db = self._db_service.get_db()
        election: ElectionDto = self._election_service.get(db, election_id)
        existing_decryptions = self._decryption_service.get_decryption_count(
            db, election_id
        )
        return eel_success(
            f"{election.election_name} Tally #{existing_decryptions + 1}"
        )

    def create_decryption(
        self, election_id: str, decryption_name: str
    ) -> dict[str, Any]:
        try:
            self._log.debug(
                f"Creating decryption for election: {election_id} with name: {decryption_name}"
            )
            db = self._db_service.get_db()
            election = self._election_service.get(db, election_id)
            if election is None:
                return eel_fail(f"Election {election_id} not found")
            name_exists = self._decryption_service.name_exists(db, decryption_name)
            if name_exists:
                return eel_fail(f"Decryption '{decryption_name}' already exists")
            decryption_id = self._decryption_service.create(
                db, election, decryption_name
            )
            self._election_service.append_decryption(
                db, election_id, decryption_id, decryption_name
            )
            return eel_success(decryption_id)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)
