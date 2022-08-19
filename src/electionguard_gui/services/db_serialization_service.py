from typing import Any
from electionguard.key_ceremony import (
    ElectionJointKey,
    ElectionPartialKeyBackup,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
)


def public_key_to_dict(key: ElectionPublicKey) -> dict[str, Any]:
    return {
        "owner_id": key.owner_id,
        "sequence_order": key.sequence_order,
        "key": str(key.key),
        "coefficient_commitments": [str(c) for c in key.coefficient_commitments],
        "coefficient_proofs": [
            {
                "public_key": str(cp.public_key),
                "commitment": str(cp.commitment),
                "challenge": str(cp.challenge),
                "response": str(cp.response),
                "usage": str(cp.usage),
            }
            for cp in key.coefficient_proofs
        ],
    }


def backup_to_dict(backup: ElectionPartialKeyBackup) -> dict[str, Any]:
    coordinate = backup.encrypted_coordinate
    return {
        "owner_id": backup.owner_id,
        "designated_id": backup.designated_id,
        "designated_sequence_order": backup.designated_sequence_order,
        "encrypted_coordinate": {
            "pad": str(coordinate.pad),
            "data": coordinate.data,
            "mac": coordinate.mac,
        },
    }


def verification_to_dict(
    verification: ElectionPartialKeyVerification,
) -> dict[str, Any]:
    return {
        "owner_id": verification.owner_id,
        "designated_id": verification.designated_id,
        "verifier_id": verification.verifier_id,
        "verified": verification.verified,
    }


def joint_key_to_dict(
    key: ElectionJointKey,
) -> dict[str, Any]:
    return {
        "joint_public_key": str(key.joint_public_key),
        "commitment_hash": str(key.commitment_hash),
    }
