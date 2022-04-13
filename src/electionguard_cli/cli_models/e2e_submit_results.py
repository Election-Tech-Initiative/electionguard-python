from typing import List
from electionguard.ballot import CiphertextBallot
from electionguard.data_store import DataStore
from electionguard.encrypt import EncryptionDevice


class E2eSubmitResults:
    """Responsible for holding the results of submitting votes in an election."""

    def __init__(
        self,
        data_store: DataStore,
        device: EncryptionDevice,
        ciphertext_ballots: List[CiphertextBallot],
    ):
        self.data_store = data_store
        self.device = device
        self.ciphertext_ballots = ciphertext_ballots

    data_store: DataStore
    device: EncryptionDevice
    ciphertext_ballots: List[CiphertextBallot]
