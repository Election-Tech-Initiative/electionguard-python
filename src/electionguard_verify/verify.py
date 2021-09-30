from dataclasses import dataclass
from typing import Optional

from electionguard.ballot import (
    CiphertextBallot,
)


@dataclass
class Verification:
    """
    Representation of a verification result with an optional message
    """

    verified: bool
    """Verification successful?"""
    message: Optional[str]


def verify_ballot(ballot: CiphertextBallot) -> Verification:
    """
    Method to verify the validity of a ballot

    TEMPORARY method that always returns True!!!
    """

    print(f"Verifying ballot {ballot.object_id}")

    return Verification(True, message=None)
