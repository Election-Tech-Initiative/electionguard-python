from os import getcwd, path
from electionguard.serialize import from_file, to_file
from electionguard.guardian import Guardian, PrivateGuardianRecord
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase
from electionguard_tools.helpers.export import GUARDIAN_PREFIX


class GuardianService(ServiceBase):
    """Responsible for functionality related to guardians"""

    _log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self._log = log_service

    def save_guardian(self, guardian: Guardian, key_ceremony: KeyCeremonyDto) -> None:
        private_guardian_record = guardian.export_private_data()
        file_name = GUARDIAN_PREFIX + private_guardian_record.guardian_id
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony.id)
        file = to_file(private_guardian_record, file_name, file_path)
        self._log.warn(
            f"Guardian private data saved to {file}. This data should be carefully protected and never shared."
        )

    def load_guardian(self, guardian_id: str, key_ceremony: KeyCeremonyDto) -> Guardian:
        file_name = GUARDIAN_PREFIX + guardian_id + ".json"
        file_path = path.join(getcwd(), "gui_private_keys", key_ceremony.id, file_name)
        self._log.debug(f"loading guardian from {file_path}")
        private_guardian_record = from_file(PrivateGuardianRecord, file_path)
        return Guardian.from_private_record(
            private_guardian_record,
            key_ceremony.guardian_count,
            key_ceremony.quorum,
        )

    def load_other_keys(
        self, key_ceremony: KeyCeremonyDto, current_user_id: str, guardian: Guardian
    ) -> None:
        current_user_other_keys = key_ceremony.find_other_keys_for_user(current_user_id)
        for other_key in current_user_other_keys:
            other_user = other_key.owner_id
            self._log.debug(f"saving other_key from {other_user} for {current_user_id}")
            guardian.save_guardian_key(other_key)


def make_guardian(
    user_id: str, guardian_number: int, key_ceremony: KeyCeremonyDto
) -> Guardian:
    return Guardian.from_nonce(
        user_id,
        guardian_number,
        key_ceremony.guardian_count,
        key_ceremony.quorum,
    )


def make_mediator(key_ceremony: KeyCeremonyDto) -> KeyCeremonyMediator:
    quorum = key_ceremony.quorum
    guardian_count = key_ceremony.guardian_count
    ceremony_details = CeremonyDetails(guardian_count, quorum)
    mediator: KeyCeremonyMediator = KeyCeremonyMediator("mediator_1", ceremony_details)
    return mediator


def announce_guardians(
    key_ceremony: KeyCeremonyDto, mediator: KeyCeremonyMediator
) -> None:
    for guardian_id in key_ceremony.guardians_joined:
        key = key_ceremony.find_key(guardian_id)
        mediator.announce(key)
