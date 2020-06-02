from typing import Dict, Optional

from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalKeyPair, elgamal_keypair_from_secret
from .group import ElementModP, ElementModQ, int_to_q
from .key_ceremony import CeremonyDetails, CeremonyParticipant

ElectionKeyPair = ElGamalKeyPair


class ElectionKeyHolder:
    _election_keys: ElectionKeyPair

    def __init__(self, election_secret: int) -> None:
        # TODO Should the key really be created here? What happens if this fails?
        secret = int_to_q(election_secret)
        if secret is None:
            return
        _election_keys = elgamal_keypair_from_secret(secret)

    # TODO Implement Encryption for Public Key
    def share_encrypted_election_public_key(self) -> ElementModP:
        return self._election_keys.public_key

    # TODO Implement Encryption for Partial Secret Key
    def share_encrypted_election_partial_secret_key(self) -> ElementModQ:
        return self._election_keys.secret_key


class ElectionKeyDistributor(CeremonyParticipant):
    _election_public_key_store: Dict[str, str]
    _election_partial_secret_key_stores: Dict[str, Dict[str, str]]

    def __init__(self, ceremony_details: CeremonyDetails) -> None:
        super().__init__(ceremony_details)

    def request_election_public_keys(self, guardian_id: str) -> Dict[str, str]:
        if (
            len(self._election_public_key_store)
            < self._ceremony_details.number_of_guardians
        ):
            raise Exception("Missing Guardians")
        if not self._election_public_key_store[guardian_id]:
            raise Exception("Guardian not present in ceremony")
        return self._election_public_key_store

    def request_election_partial_secret_keys(self, guardian_id: str) -> Dict[str, str]:
        if (
            len(self._election_partial_secret_key_stores)
            < self._ceremony_details.number_of_guardians
        ):
            raise Exception("Missing Guardians")
        if not self._election_partial_secret_key_stores[guardian_id]:
            raise Exception("Guardian not present in ceremony")
        return Dict[str, str]()

    def add_public_key_store(self) -> None:
        return

    def add_partial_private_key_store(self, guardian_id: str) -> None:
        print(guardian_id)
        return


class ElectionKeyProtector(
    ElectionObjectBase, ElectionPublicKeyStore, ElectionPartialSecretKeyStore
):
    """
    Protector of the election public and partial secret keys
    """

    def __init__(self, id: str):
        super().__init__(id)


class ElectionPublicKeyStore:
    _encrypted_public_key_store: Dict[str, Optional[str]]

    # @property
    # def encrypted_public_keys(self) -> Dict[str, str]:
    #     return self._encrypted_public_keys


class ElectionPartialSecretKeyStore:
    _encrypted_partial_secret_key_store: Dict[str, Optional[str]]

    # @property
    # def encrypted_partial_secret_keys(self) -> Dict[str, str]:
    #     return self._encrypted_partial_secret_keys
