from dataclasses import dataclass
from typing import Optional

from electionguard.ballot import (
    CiphertextBallot,
)
from electionguard.election import CiphertextElectionContext
from electionguard.manifest import (
    Manifest,
)


@dataclass
class Verification:
    """
    Representation of a verification result with an optional message
    """

    verified: bool
    """Verification successful?"""
    message: Optional[str]


def verify_ballot(
    ballot: CiphertextBallot,
    manifest: Manifest,
    context: CiphertextElectionContext,
) -> Verification:
    """
    Method to verify the validity of a ballot
    """

    if not ballot.is_valid_encryption(
        manifest.crypto_hash(),
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        return Verification(
            False,
            message=f"verify_ballot: mismatching ballot encryption {ballot.object_id}",
        )

    return Verification(True, message=None)
