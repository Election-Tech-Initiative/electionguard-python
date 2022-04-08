from electionguard.data_store import DataStore
from electionguard.encrypt import EncryptionDevice


class E2eSubmitResults:
    """Responsible for holding the results of submitting votes in an election."""

    def __init__(self, data_store: DataStore, device: EncryptionDevice):
        self.data_store = data_store
        self.device = device

    data_store: DataStore
    device: EncryptionDevice
