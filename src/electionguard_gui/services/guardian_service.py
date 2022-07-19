from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard_gui.models.key_ceremony_dto import KeyCeremonyDto


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
