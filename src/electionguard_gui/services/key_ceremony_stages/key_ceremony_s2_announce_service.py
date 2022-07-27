from typing import Any, List
from pymongo.database import Database
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.utils import get_optional
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.models.key_ceremony_states import KeyCeremonyStates
from electionguard_gui.services.db_serialization_service import public_key_to_dict
from electionguard_gui.services.guardian_service import (
    announce_guardians,
    make_mediator,
)
from electionguard_gui.services.key_ceremony_stages.key_ceremony_stage_base import (
    KeyCeremonyStageBase,
)


class KeyCeremonyS2AnnounceService(KeyCeremonyStageBase):
    """Responsible for stage 2 of the key ceremony where admins announce the key ceremony"""

    def should_run(
        self, key_ceremony: KeyCeremonyDto, state: KeyCeremonyStates
    ) -> bool:
        is_admin = self._auth_service.is_admin()
        should_run: bool = is_admin and state == KeyCeremonyStates.PendingAdminAnnounce
        return should_run

    def run(self, db: Database, key_ceremony: KeyCeremonyDto) -> None:
        key_ceremony_id = key_ceremony.id
        self.log.info("all guardians have joined, announcing guardians")
        other_keys = self.announce(key_ceremony)
        self.log.debug("saving other_keys")
        self._key_ceremony_service.append_other_key(db, key_ceremony_id, other_keys)
        self._key_ceremony_service.notify_changed(db, key_ceremony_id)

    def announce(self, key_ceremony: KeyCeremonyDto) -> List[dict[str, Any]]:
        other_keys = []
        mediator = make_mediator(key_ceremony)
        announce_guardians(key_ceremony, mediator)
        for guardian_id in key_ceremony.guardians_joined:
            self.log.debug(f"announcing guardian {guardian_id}")
            other_guardian_keys: List[ElectionPublicKey] = get_optional(
                mediator.share_announced(guardian_id)
            )
            other_keys.append(
                {
                    "owner_id": guardian_id,
                    "other_keys": [
                        public_key_to_dict(key) for key in other_guardian_keys
                    ],
                }
            )
        return other_keys
