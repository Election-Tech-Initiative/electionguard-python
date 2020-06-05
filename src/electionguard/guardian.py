from typing import Callable, Optional, Tuple
from secrets import randbelow

from .chaum_pedersen import ChaumPedersenProof, make_chaum_pedersen
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext
from .group import ElementModP, ElementModQ, Q, int_to_q_unchecked
from .key_ceremony import (
    AuxiliaryKeyPair,
    AuxiliaryPublicKey,
    AuxiliaryDecrypt,
    AuxiliaryEncrypt,
    combine_election_public_keys,
    CeremonyDetails,
    default_auxiliary_decrypt,
    default_auxiliary_encrypt,
    ElectionJointKey,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    generate_elgamal_auxiliary_key_pair,
    GuardianId,
    GuardianDataStore,
    PublicKeySet,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from .nonces import Nonces


class Guardian(ElectionObjectBase):
    sequence_order: int
    ceremony_details: CeremonyDetails
    _auxiliary_keys: AuxiliaryKeyPair
    _election_keys: ElectionKeyPair
    _backups_to_share: GuardianDataStore[GuardianId, ElectionPartialKeyBackup]

    # From Other Guardians
    _guardian_auxiliary_public_keys: GuardianDataStore[GuardianId, AuxiliaryPublicKey]
    _guardian_election_public_keys: GuardianDataStore[GuardianId, ElectionPublicKey]
    _guardian_election_partial_key_backups: GuardianDataStore[
        GuardianId, ElectionPartialKeyBackup
    ]
    _guardian_election_partial_key_verifications: GuardianDataStore[
        GuardianId, ElectionPartialKeyVerification
    ]

    def __init__(
        self, id: str, sequence_order: int, number_of_guardians: int, quorum: int,
    ) -> None:

        super().__init__(id)
        self.sequence_order = sequence_order
        self.set_ceremony_details(number_of_guardians, quorum)
        self._backups_to_share = GuardianDataStore[
            GuardianId, ElectionPartialKeyBackup
        ]()
        self._guardian_auxiliary_public_keys = GuardianDataStore[
            GuardianId, AuxiliaryPublicKey
        ]()
        self._guardian_election_public_keys = GuardianDataStore[
            GuardianId, ElectionPublicKey
        ]()
        self._guardian_election_partial_key_backups = GuardianDataStore[
            GuardianId, ElectionPartialKeyBackup
        ]()
        self._guardian_election_partial_key_verifications = GuardianDataStore[
            GuardianId, ElectionPartialKeyVerification
        ]()

        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair()

    def reset(self, number_of_guardians: int, quorum: int) -> None:
        self._backups_to_share.clear()
        self._guardian_auxiliary_public_keys.clear()
        self._guardian_election_public_keys.clear()
        self._guardian_election_partial_key_backups.clear()
        self._guardian_election_partial_key_verifications.clear()
        self.set_ceremony_details(number_of_guardians, quorum)
        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair()

    # Ceremony
    def set_ceremony_details(self, number_of_guardians: int, quorum: int) -> None:
        self.ceremony_details = CeremonyDetails(number_of_guardians, quorum)

    # Public Keys
    def share_public_keys(self) -> PublicKeySet:
        return PublicKeySet(
            self.object_id,
            self.sequence_order,
            self._auxiliary_keys.public_key,
            self._election_keys.key_pair.public_key,
            self._election_keys.proof,
        )

    def save_guardian_public_keys(self, shared_key_set: PublicKeySet) -> None:
        self.save_auxiliary_public_key(
            AuxiliaryPublicKey(
                shared_key_set.owner_id,
                shared_key_set.sequence_order,
                shared_key_set.auxiliary_public_key,
            )
        )
        self.save_election_public_key(
            ElectionPublicKey(
                shared_key_set.owner_id,
                shared_key_set.election_public_key_proof,
                shared_key_set.election_public_key,
            ),
        )

    def all_public_keys_received(self) -> bool:
        return (
            self.all_auxiliary_public_keys_received()
            and self.all_election_public_keys_received()
        )

    # Auxiliary Key Pair
    def generate_auxiliary_key_pair(
        self,
        generate_auxiliary_key_pair: Callable[
            [], AuxiliaryKeyPair
        ] = generate_elgamal_auxiliary_key_pair,
    ) -> None:
        self._auxiliary_keys = generate_auxiliary_key_pair()
        self.save_auxiliary_public_key(self.share_auxiliary_public_key())

    def share_auxiliary_public_key(self) -> AuxiliaryPublicKey:
        return AuxiliaryPublicKey(
            self.object_id, self.sequence_order, self._auxiliary_keys.public_key
        )

    def save_auxiliary_public_key(self, shared_key: AuxiliaryPublicKey) -> None:
        self._guardian_auxiliary_public_keys.set(shared_key.owner_id, shared_key)

    def all_auxiliary_public_keys_received(self) -> bool:
        return (
            self._guardian_auxiliary_public_keys.length()
            == self.ceremony_details.number_of_guardians
        )

    # Election Key Pair
    def generate_election_key_pair(self) -> None:
        self._election_keys = generate_election_key_pair(self.ceremony_details.quorum)
        self.save_election_public_key(self.share_election_public_key())

    def share_election_public_key(self) -> ElectionPublicKey:
        return ElectionPublicKey(
            self.object_id,
            self._election_keys.proof,
            self._election_keys.key_pair.public_key,
        )

    def save_election_public_key(self, shared_key: ElectionPublicKey) -> None:
        self._guardian_election_public_keys.set(shared_key.owner_id, shared_key)

    def all_election_public_keys_received(self) -> bool:
        return (
            self._guardian_election_public_keys.length()
            == self.ceremony_details.number_of_guardians
        )

    def generate_election_partial_key_backups(
        self, encrypt: AuxiliaryEncrypt = default_auxiliary_encrypt
    ) -> None:
        if not self.all_auxiliary_public_keys_received():
            return
        for auxiliary_key in self._guardian_auxiliary_public_keys.values():
            backup = generate_election_partial_key_backup(
                self.object_id, self._election_keys.polynomial, auxiliary_key, encrypt
            )
            self._backups_to_share.set(auxiliary_key.owner_id, backup)

    # Election Partial Key Backup
    def share_election_partial_key_backup(
        self, designated_id: str
    ) -> Optional[ElectionPartialKeyBackup]:
        return self._backups_to_share.get(designated_id)

    def save_election_partial_key_backup(
        self, backup: ElectionPartialKeyBackup
    ) -> None:
        self._guardian_election_partial_key_backups.set(backup.owner_id, backup)

    def all_election_partial_key_backups_received(self) -> bool:
        return (
            self._guardian_election_partial_key_backups.length()
            == self.ceremony_details.number_of_guardians - 1
        )

    # Verification
    def verify_election_partial_key_backup(
        self, guardian_id: str, decrypt: AuxiliaryDecrypt = default_auxiliary_decrypt
    ) -> Optional[ElectionPartialKeyVerification]:
        backup = self._guardian_election_partial_key_backups.get(guardian_id)
        if backup is None:
            return None
        return verify_election_partial_key_backup(
            self.object_id, backup, self._auxiliary_keys, decrypt
        )

    def publish_election_backup_challenge(
        self, guardian_id: str
    ) -> Optional[ElectionPartialKeyChallenge]:
        backup_in_question = self._backups_to_share.get(guardian_id)
        if backup_in_question is None:
            return None
        return generate_election_partial_key_challenge(
            backup_in_question, self._election_keys.polynomial
        )

    def verify_election_partial_key_challenge(
        self, challenge: ElectionPartialKeyChallenge
    ) -> ElectionPartialKeyVerification:
        return verify_election_partial_key_challenge(self.object_id, challenge)

    def save_election_partial_key_verification(
        self, verification: ElectionPartialKeyVerification
    ) -> None:
        self._guardian_election_partial_key_verifications.set(
            verification.designated_id, verification
        )

    def all_election_partial_key_backups_verified(self) -> bool:
        required = self.ceremony_details.number_of_guardians - 1
        if self._guardian_election_partial_key_verifications.length() != required:
            return False
        for verified in self._guardian_election_partial_key_verifications.values():
            if not verified:
                return False
        return True

    # Joint Key
    def publish_joint_key(self) -> Optional[ElectionJointKey]:
        if not self.all_election_public_keys_received():
            return None
        if not self.all_election_partial_key_backups_verified():
            return None
        return combine_election_public_keys(self._guardian_election_public_keys)

    def partial_decrypt(
        self,
        elgamal_encryption: ElGamalCiphertext,
        extended_base_hash: ElementModQ,
        nonce_seed: ElementModQ = None,
    ) -> Tuple[ElementModP, ChaumPedersenProof]:
        if nonce_seed is None:
            nonce_seed = int_to_q_unchecked(randbelow(Q))

        # 𝑀𝑖
        partial_decryption = elgamal_encryption.partial_decrypt(
            self._election_keys.key_pair.secret_key
        )
        # 𝑀 =𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
        proof = make_chaum_pedersen(
            message=elgamal_encryption,
            s=self._election_keys.key_pair.secret_key,
            m=partial_decryption,
            seed=nonce_seed,
            hash_header=extended_base_hash,
        )

        return (partial_decryption, proof)
