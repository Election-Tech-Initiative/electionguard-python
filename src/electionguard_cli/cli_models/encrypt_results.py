from typing import List
from electionguard.ballot import CiphertextBallot
from electionguard.encrypt import EncryptionDevice


class EncryptResults:
    """Responsible for holding the results of encrypting votes in an election."""

    def __init__(
        self,
        device: EncryptionDevice,
        ciphertext_ballots: List[CiphertextBallot],
    ):
        self.device = device
        self.ciphertext_ballots = ciphertext_ballots

    device: EncryptionDevice
    ciphertext_ballots: List[CiphertextBallot]
