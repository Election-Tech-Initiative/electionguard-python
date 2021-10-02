from dataclasses import dataclass
from typing import Optional

from electionguard.ballot import (
    SubmittedBallot,
    is_valid_encryption,
)


@dataclass
class Verification:
    """
    Representation of a verification result with an optional message
    """

    verified: bool
    """Verification successful?"""
    message: Optional[str]


def verify_ballot(ballot: SubmittedBallot) -> Verification:
    """
    Method to verify the proofs of a ballot
    TEMPORARY method that always returns True!!!
    """
    
    if(is_valid_encryption):
      return Verification(True, message=None)
