from typing import Any, List
from datetime import datetime
from electionguard.key_ceremony import ElectionPublicKey

from electionguard_gui.eel_utils import utc_to_str
from electionguard_gui.services.db_serialization_service import (
    dict_to_election_public_key,
)

# pylint: disable=too-many-instance-attributes
class KeyCeremonyDto:
    """A key ceremony for serializing to the front-end GUI and providing helper functions to Python."""

    def __init__(self, key_ceremony: Any):
        self.id = str(key_ceremony["_id"])
        self.guardian_count = key_ceremony["guardian_count"]
        self.key_ceremony_name = key_ceremony["key_ceremony_name"]
        self.quorum = key_ceremony["quorum"]
        self.guardians_joined = key_ceremony["guardians_joined"]
        self.other_keys = key_ceremony["other_keys"]
        self.backups = key_ceremony["backups"]
        self.created_by = key_ceremony["created_by"]
        self.created_at_utc = key_ceremony["created_at"]
        self.created_at_str = utc_to_str(self.created_at_utc)
        self.keys = [dict_to_election_public_key(key) for key in key_ceremony["keys"]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "guardian_count": self.guardian_count,
            "quorum": self.quorum,
            "key_ceremony_name": self.key_ceremony_name,
            "status": self.status,
            "created_by": self.created_by,
            "created_at_str": self.created_at_str,
            "guardians_joined": self.guardians_joined,
            "can_join": self.can_join,
        }

    id: str
    guardians_joined: List[str]
    key_ceremony_name: str
    created_by: str
    created_at_utc: datetime
    can_join: bool
    keys: List[ElectionPublicKey]
    guardian_count: int
    quorum: int
    other_keys: List[Any]
    backups: List[Any]
    status: str

    def find_key(self, guardian_id: str) -> ElectionPublicKey:
        keys = self.keys
        return next(key for key in keys if key.owner_id == guardian_id)

    def get_backups_for_user(self, user_id: str) -> List[Any]:
        return [backup for backup in self.backups if backup["owner_id"] == user_id]

    def find_other_keys_for_user(self, user_id: str) -> List[ElectionPublicKey]:
        other_key_wrapper = next(
            filter(
                lambda other_key: other_key["owner_id"] == user_id,
                self.other_keys,
            )
        )
        other_keys = other_key_wrapper["other_keys"]
        return [dict_to_election_public_key(other_key) for other_key in other_keys]
