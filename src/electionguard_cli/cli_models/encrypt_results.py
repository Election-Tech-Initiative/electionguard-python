from dataclasses import dataclass
from typing import List
from electionguard.ballot import CiphertextBallot
from electionguard.encrypt import EncryptionDevice


@dataclass
class EncryptResults:
    """Responsible for holding the results of encrypting votes in an election."""

    device: EncryptionDevice
    ciphertext_ballots: List[CiphertextBallot]
