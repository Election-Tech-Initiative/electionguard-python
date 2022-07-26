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
        return eel_success(election.election_name + " #1")

    def create_decryption(self, election_id: str, name: str) -> dict[str, Any]:
        try:
            self._log.debug(
                f"Creating decryption for election: {election_id} with name: {name}"
            )
            db = self._db_service.get_db()
            election = self._election_service.get(db, election_id)
            if election is None:
                return eel_fail(f"Election {election_id} not found")
            decryption = self._decryption_service.get_by_name(db, name)
            if decryption is not None:
                return eel_fail(f"Decryption '{name}' already exists")
            decryption_id = self._decryption_service.create(db, election_id, name)
            self._election_service.append_decryption(
                db, election_id, decryption_id, name
            )
            return eel_success(decryption_id)
        # pylint: disable=broad-except
        except Exception as e:
            self._log.error(e)
            return eel_fail(str(e))
