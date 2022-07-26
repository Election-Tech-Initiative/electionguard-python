from typing import Any
import eel
from electionguard_gui.eel_utils import eel_fail, eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import ElectionService, DecryptionService


class ViewDecryptionComponent(ComponentBase):
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
        eel.expose(self.get_decryption)

    def get_decryption(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            return eel_success(decryption.to_dict())
        # pylint: disable=broad-except
        except Exception as e:
            self._log.error(e)
            return eel_fail(str(e))
