from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import ElectionService, DecryptionService
from electionguard_gui.services.decryption_stages import DecryptionS1JoinService


class ViewDecryptionComponent(ComponentBase):
    """Responsible for functionality related to creating decryptions for an election"""

    _decryption_service: DecryptionService
    _election_service: ElectionService
    _decryption_s1_join_service: DecryptionS1JoinService

    def __init__(
        self,
        decryption_service: DecryptionService,
        election_service: ElectionService,
        decryption_s1_join_service: DecryptionS1JoinService,
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service
        self._decryption_s1_join_service = decryption_s1_join_service

    def expose(self) -> None:
        eel.expose(self.get_decryption)
        eel.expose(self.join_decryption)

    def get_decryption(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            return eel_success(decryption.to_dict())
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)

    def join_decryption(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            decryption = self._decryption_service.get(db, decryption_id)
            self._decryption_s1_join_service.run(db, decryption)
            return eel_success(decryption.to_dict())
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)
