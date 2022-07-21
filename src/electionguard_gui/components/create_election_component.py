from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import KeyCeremonyService


class CreateElectionComponent(ComponentBase):
    """Responsible for functionality related to creating encryption packages for elections"""

    _key_ceremony_service: KeyCeremonyService

    def __init__(self, key_ceremony_service: KeyCeremonyService) -> None:
        self._key_ceremony_service = key_ceremony_service

    def expose(self) -> None:
        eel.expose(self.get_keys)
        eel.expose(self.create_election)

    def get_keys(self) -> dict[str, Any]:
        self._log.debug("Getting keys")
        db = self._db_service.get_db()
        completed_key_ceremonies = self._key_ceremony_service.get_completed(db)
        keys = [
            key_ceremony.to_id_name_dict() for key_ceremony in completed_key_ceremonies
        ]
        return eel_success(keys)

    def create_election(
        self, key_ceremony_id: str, election_name: str, manifest: str, url: str
    ) -> dict[str, Any]:
        self._log.debug(
            f"Creating election key_ceremony_id: {key_ceremony_id}, election_name: {election_name}, manifest: {manifest}, url: {url}"
        )
        # db = self._db_service.get_db()
        # key_ceremony = self._key_ceremony_service.get_by_id(db, key_ceremony_id)
        # election = self._key_ceremony_service.create_election(
        #     db, key_ceremony, election_name, manifest
        # )
        return eel_success("success")
