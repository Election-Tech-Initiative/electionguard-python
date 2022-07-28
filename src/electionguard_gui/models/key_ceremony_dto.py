from typing import Any, List
from datetime import datetime
from electionguard import ElectionPartialKeyVerification
from electionguard.group import ElementModP, ElementModQ
from electionguard.key_ceremony import (
    ElectionJointKey,
    ElectionPartialKeyBackup,
    ElectionPublicKey,
)
from electionguard.election_polynomial import PublicCommitment
from electionguard.elgamal import ElGamalPublicKey, HashedElGamalCiphertext
from electionguard.schnorr import SchnorrProof

from electionguard_gui.eel_utils import utc_to_str
from electionguard_gui.services.authorization_service import AuthorizationService

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
        self.shared_backups = key_ceremony["shared_backups"]
        self.verifications = key_ceremony["verifications"]
        self.keys = [_dict_to_election_public_key(key) for key in key_ceremony["keys"]]
        self.joint_key = key_ceremony["joint_key"]
        self.created_by = key_ceremony["created_by"]
        self.created_at_utc = key_ceremony["created_at"]
        self.created_at_str = utc_to_str(key_ceremony["created_at"])
        self.completed_at_utc = key_ceremony["completed_at"]
        self.completed_at_str = utc_to_str(key_ceremony["completed_at"])

    def to_id_name_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key_ceremony_name": self.key_ceremony_name,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "guardian_count": self.guardian_count,
            "key_ceremony_name": self.key_ceremony_name,
            "quorum": self.quorum,
            "guardians_joined": self.guardians_joined,
            "created_by": self.created_by,
            "created_at_str": self.created_at_str,
            "completed_at_str": self.completed_at_str,
            "can_join": self.can_join,
            "status": self.status,
        }

    id: str
    guardian_count: int
    key_ceremony_name: str
    quorum: int
    guardians_joined: List[str]
    other_keys: List[Any]
    backups: List[Any]
    shared_backups: List[Any]
    verifications: List[Any]
    keys: List[ElectionPublicKey]
    joint_key: Any
    created_by: str
    created_at_utc: datetime
    completed_at_utc: datetime
    created_at_str: str
    completed_at_str: str
    can_join: bool
    status: str

    def find_key(self, guardian_id: str) -> ElectionPublicKey:
        keys = self.keys
        key = next((key for key in keys if key.owner_id == guardian_id), None)
        if key is None:
            raise Exception("Key not found for guardian: " + guardian_id)
        return key

    def get_backup_count_for_user(self, user_id: str) -> int:
        backups = [backup for backup in self.backups if backup["owner_id"] == user_id]
        return len(backups)

    def get_verification_count_for_user(self, user_id: str) -> int:
        return len(
            [
                verification
                for verification in self.verifications
                if verification["designated_id"] == user_id
            ]
        )

    def get_verifications(self) -> List[ElectionPartialKeyVerification]:
        return [
            _dict_to_verification(verification) for verification in self.verifications
        ]

    def get_shared_backups_for_guardian(
        self, guardian_id: str
    ) -> List[ElectionPartialKeyBackup]:
        shared_backup_wrapper = next(
            filter(
                lambda backup: backup["owner_id"] == guardian_id, self.shared_backups
            )
        )
        backups = shared_backup_wrapper["backups"]
        return [_dict_to_backup(backup) for backup in backups]

    def get_backups(self) -> List[ElectionPartialKeyBackup]:
        return [_dict_to_backup(backup) for backup in self.backups]

    def find_other_keys_for_user(self, user_id: str) -> List[ElectionPublicKey]:
        other_key_wrapper = next(
            filter(
                lambda other_key: other_key["owner_id"] == user_id,
                self.other_keys,
            )
        )
        other_keys = other_key_wrapper["other_keys"]
        return [_dict_to_election_public_key(other_key) for other_key in other_keys]

    def joint_key_exists(self) -> bool:
        return self.joint_key is not None

    def get_joint_key(self) -> ElectionJointKey:
        return ElectionJointKey(
            ElGamalPublicKey(self.joint_key["joint_public_key"]),
            ElementModQ(self.joint_key["commitment_hash"]),
        )

    def set_can_join(self, auth_service: AuthorizationService) -> None:
        user_id = auth_service.get_user_id()
        already_joined = user_id in self.guardians_joined
        is_admin = auth_service.is_admin()
        self.can_join = not already_joined and not is_admin


def _dict_to_verification(verification: Any) -> ElectionPartialKeyVerification:
    return ElectionPartialKeyVerification(
        verification["owner_id"],
        verification["designated_id"],
        verification["verifier_id"],
        verification["verified"],
    )


def _dict_to_backup(backup: Any) -> ElectionPartialKeyBackup:
    coordinate = backup["encrypted_coordinate"]
    ciphertext = HashedElGamalCiphertext(
        ElementModP(coordinate["pad"]), coordinate["data"], coordinate["mac"]
    )
    return ElectionPartialKeyBackup(
        backup["owner_id"],
        backup["designated_id"],
        backup["designated_sequence_order"],
        ciphertext,
    )


def _dict_to_election_public_key(key: Any) -> ElectionPublicKey:
    coefficient_commitments = [
        PublicCommitment(x) for x in key["coefficient_commitments"]
    ]
    coefficient_proofs = [
        SchnorrProof(
            cp["public_key"],
            cp["commitment"],
            cp["challenge"],
            cp["response"],
            cp["usage"],
        )
        for cp in key["coefficient_proofs"]
    ]
    guardian_public_key = ElectionPublicKey(
        key["owner_id"],
        key["sequence_order"],
        ElGamalPublicKey(key["key"]),
        coefficient_commitments,
        coefficient_proofs,
    )
    return guardian_public_key
