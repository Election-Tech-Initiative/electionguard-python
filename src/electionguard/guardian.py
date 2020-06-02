from typing import Callable, Dict, Tuple

from .auxiliary_key_pair import AuxiliaryKeyPair, AuxiliaryDecrypt, AuxiliaryEncrypt
from .election_key_pair import ElectionKeyPair
from .election_object_base import ElectionObjectBase
from .key_ceremony import generate_election_keys, CeremonyDetails
from .key_share import share_public_key, share_secret_key, SharedKey
from .key_store import KeyStore


# TODO Inject classes instead of multiple inheritance. Maybe builder pattern
class Guardian(ElectionObjectBase):
    ceremony_details: CeremonyDetails
    _auxiliary_keys: AuxiliaryKeyPair
    _election_keys: ElectionKeyPair

    # keys that a guardian
    _shareable_election_secret_keys: Dict[str, Tuple[str, bool]]

    # From Other Guardians
    _auxiliary_public_key_store: KeyStore
    _election_public_key_store: KeyStore
    _election_secret_key_store: KeyStore

    def __init__(
        self,
        id: str,
        number_of_guardians: int,
        quorum: int,
        generate_auxiliary_keys: Callable[[], AuxiliaryKeyPair],
    ) -> None:

        super().__init__(id)

        self.ceremony_details = Tuple[number_of_guardians, quorum]

        self._auxiliary_keys = generate_auxiliary_keys()
        self._auxiliary_public_key_store.set(
            self.object_id, self._auxiliary_keys.public_key
        )

        self._election_keys = generate_election_keys()
        self._election_public_key_store.set(self.object_id)
        self._election_secret_key_store.set(self.object_id)

    # AUXILIARY
    def auxiliary_decrypt(self, message: str, decrypt: AuxiliaryDecrypt) -> str:
        return decrypt(message, self._auxiliary_keys)

    def auxiliary_encrypt(self, message: str, encrypt: AuxiliaryEncrypt) -> str:
        return encrypt(message, self._auxiliary_keys)

    def share_auxiliary_public_key(self, recipient_id: str) -> SharedKey:
        return share_public_key(
            self.object_id, recipient_id, self._auxiliary_keys.public_key
        )

    # ELECTION
    def share_election_public_key(self, recipient_id: str) -> SharedKey:
        return share_public_key(
            self.object_id, recipient_id, str(self._election_keys.public_key.to_int())
        )

    def store_election_public_key(self, guardian_id: str, key: str) -> None:
        self._election_public_key_store.set(guardian_id, key)

    # TODO Implement Generation of private shared partial secret key prior to share.
    def share_election_partial_secret_key(self, recipient_id: str) -> SharedKey:
        return share_secret_key(
            self.object_id, recipient_id, str(self._election_keys.secret_key.to_int())
        )

    def store_election_secret_key(self, guardian_id: str, partial_key: str) -> None:
        self._election_public_key_store.set(guardian_id, partial_key)

    def receive_election_partial_secret_key_verification(self) -> None:
        """
        Receive a single trustees verification of the shares
        """
        return

    def verify_trustee_share_verification_received(self) -> None:
        """
        Verify all trustees have verified their received shares
        """
        return
