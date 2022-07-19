from typing import Any

from electionguard.guardian import Guardian


def make_guardian(user_id: str, guardian_number: int, key_ceremony: Any) -> Guardian:
    return Guardian.from_nonce(
        user_id,
        guardian_number,
        key_ceremony["guardian_count"],
        key_ceremony["quorum"],
    )
