from typing import Callable, Optional, Tuple

from .chaum_pedersen import ChaumPedersenProof, make_chaum_pedersen
from .data_store import DataStore, ReadOnlyDataStore
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext
from .group import (
    ElementModP,
    ElementModQ,
    int_to_q,
    mult_p,
    pow_q,
    pow_p,
    ONE_MOD_P,
    rand_q,
)
from .key_ceremony import (
    AuxiliaryKeyPair,
    AuxiliaryPublicKey,
    AuxiliaryDecrypt,
    AuxiliaryEncrypt,
    combine_election_public_keys,
    CeremonyDetails,
    CoefficientValidationSet,
    ElectionJointKey,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    get_coefficient_validation_set,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    generate_rsa_auxiliary_key_pair,
    PublicKeySet,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from .logs import log_warning
from .rsa import rsa_encrypt, rsa_decrypt
from .types import GUARDIAN_ID
from .utils import get_optional


class Guardian(ElectionObjectBase):
    """
    Guardian of election responsible for safeguarding information and decrypting results
    """

    sequence_order: int
    ceremony_details: CeremonyDetails
    _auxiliary_keys: AuxiliaryKeyPair
    _election_keys: ElectionKeyPair
    _backups_to_share: DataStore[GUARDIAN_ID, ElectionPartialKeyBackup]
    """
    The collection of this guardian's partial key backups that will be shared to other guardians
    """

    # From Other Guardians
    _guardian_auxiliary_public_keys: DataStore[GUARDIAN_ID, AuxiliaryPublicKey]
    """
    The collection of other guardians' auxiliary public keys that are shared with this guardian
    """

    _guardian_election_public_keys: DataStore[GUARDIAN_ID, ElectionPublicKey]
    """
    The collection of other guardians' election public keys that are shared with this guardian
    """

    _guardian_election_partial_key_backups: DataStore[
        GUARDIAN_ID, ElectionPartialKeyBackup
    ]
    """
    The collection of other guardians' partial key backups that are shared with this guardian
    """

    _guardian_election_partial_key_verifications: DataStore[
        GUARDIAN_ID, ElectionPartialKeyVerification
    ]
    """
    The collection of other guardians' verifications that they shared their backups correctly
    """

    def __init__(
        self,
        id: str,
        sequence_order: int,
        number_of_guardians: int,
        quorum: int,
        nonce_seed: Optional[ElementModQ] = None,
    ) -> None:
        """
        Initialize a guardian with the specified arguments

        :param id: the unique identifier for the guardian
        :param sequence_order: a unique number in [0, 256) that identifies this guardian
        :param number_of_guardians: the total number of guardians that will participate in the election
        :param quorum: the count of guardians necessary to decrypt
        :param nonce_seed: an optional `ElementModQ` value that can be used to generate the `ElectionKeyPair`.  
                           It is recommended to only use this field for testing.
        """

        super().__init__(id)
        self.sequence_order = sequence_order
        self.set_ceremony_details(number_of_guardians, quorum)
        self._backups_to_share = DataStore[GUARDIAN_ID, ElectionPartialKeyBackup]()
        self._guardian_auxiliary_public_keys = DataStore[
            GUARDIAN_ID, AuxiliaryPublicKey
        ]()
        self._guardian_election_public_keys = DataStore[
            GUARDIAN_ID, ElectionPublicKey
        ]()
        self._guardian_election_partial_key_backups = DataStore[
            GUARDIAN_ID, ElectionPartialKeyBackup
        ]()
        self._guardian_election_partial_key_verifications = DataStore[
            GUARDIAN_ID, ElectionPartialKeyVerification
        ]()

        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair(nonce_seed if nonce_seed is not None else None)

    def reset(self, number_of_guardians: int, quorum: int) -> None:
        """
        Reset guardian to initial state
        :param number_of_guardians: Number of guardians in election
        :param quorum: Quorum of guardians required to decrypt
        """
        self._backups_to_share.clear()
        self._guardian_auxiliary_public_keys.clear()
        self._guardian_election_public_keys.clear()
        self._guardian_election_partial_key_backups.clear()
        self._guardian_election_partial_key_verifications.clear()
        self.set_ceremony_details(number_of_guardians, quorum)
        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair()

    def set_ceremony_details(self, number_of_guardians: int, quorum: int) -> None:
        """
        Set ceremony details for election
        :param number_of_guardians: Number of guardians in election
        :param quorum: Quorum of guardians required to decrypt
        """
        self.ceremony_details = CeremonyDetails(number_of_guardians, quorum)

    # Public Keys
    def share_public_keys(self) -> PublicKeySet:
        """
        Share public election and auxiliary keys for guardian
        :return: Public set of election and auxiliary keys
        """
        return PublicKeySet(
            self.object_id,
            self.sequence_order,
            self._auxiliary_keys.public_key,
            self._election_keys.key_pair.public_key,
            self._election_keys.proof,
        )

    def save_guardian_public_keys(self, public_key_set: PublicKeySet) -> None:
        """
        Save public election and auxiliary keys for another guardian
        :param public_key_set: Public set of election and auxiliary keys
        """
        self.save_auxiliary_public_key(
            AuxiliaryPublicKey(
                public_key_set.owner_id,
                public_key_set.sequence_order,
                public_key_set.auxiliary_public_key,
            )
        )
        self.save_election_public_key(
            ElectionPublicKey(
                public_key_set.owner_id,
                public_key_set.election_public_key_proof,
                public_key_set.election_public_key,
            ),
        )

    def all_public_keys_received(self) -> bool:
        """
        True if all election and auxiliary public keys have been received.
        :return: All election and auxiliary public keys backups received
        """
        return (
            self.all_auxiliary_public_keys_received()
            and self.all_election_public_keys_received()
        )

    def generate_auxiliary_key_pair(
        self,
        generate_auxiliary_key_pair: Callable[
            [], AuxiliaryKeyPair
        ] = generate_rsa_auxiliary_key_pair,
    ) -> None:
        """
        Generate auxiliary key pair
        :param generate_auxiliary_key_pair: Function to generate auxiliary key pair
        """
        self._auxiliary_keys = generate_auxiliary_key_pair()
        self.save_auxiliary_public_key(self.share_auxiliary_public_key())

    def share_auxiliary_public_key(self) -> AuxiliaryPublicKey:
        """
        Share auxiliary public key with another guardian
        :return: Auxiliary Public Key
        """
        return AuxiliaryPublicKey(
            self.object_id, self.sequence_order, self._auxiliary_keys.public_key
        )

    def save_auxiliary_public_key(self, key: AuxiliaryPublicKey) -> None:
        """
        Save a guardians auxiliary public key
        :param key: Auxiliary public key
        """
        self._guardian_auxiliary_public_keys.set(key.owner_id, key)

    def all_auxiliary_public_keys_received(self) -> bool:
        """
        True if all auxiliary public keys have been received.
        :return: All auxiliary public keys backups received
        """
        return (
            len(self._guardian_auxiliary_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def guardian_auxiliary_public_keys(
        self,
    ) -> ReadOnlyDataStore[GUARDIAN_ID, AuxiliaryPublicKey]:
        """
        Get a read-only view of the auxiliary public keys provided to this Guardian
        """
        return ReadOnlyDataStore(self._guardian_auxiliary_public_keys)

    def generate_election_key_pair(self, nonce: ElementModQ = None) -> None:
        """
        Generate election key pair for encrypting/decrypting election
        """
        self._election_keys = generate_election_key_pair(
            self.ceremony_details.quorum, nonce
        )
        self.save_election_public_key(self.share_election_public_key())

    def share_election_public_key(self) -> ElectionPublicKey:
        """
        Share election public key with another guardian
        :return: Election public key
        """
        return ElectionPublicKey(
            self.object_id,
            self._election_keys.proof,
            self._election_keys.key_pair.public_key,
        )

    def share_coefficient_validation_set(self) -> CoefficientValidationSet:
        """
        Share coefficient validation set to be used for validating the coefficients post election
        """
        return get_coefficient_validation_set(
            self.object_id, self._election_keys.polynomial
        )

    def save_election_public_key(self, key: ElectionPublicKey) -> None:
        """
        Save a guardians election public key
        :param key: Election public key
        """
        self._guardian_election_public_keys.set(key.owner_id, key)

    def all_election_public_keys_received(self) -> bool:
        """
        True if all election public keys have been received.
        :return: All election public keys backups received
        """
        return (
            len(self._guardian_election_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def guardian_election_public_keys(
        self,
    ) -> ReadOnlyDataStore[GUARDIAN_ID, ElectionPublicKey]:
        """
        Get a read-only view of the Guardian Election Public Keys shared with this Guardian

        """
        return ReadOnlyDataStore(self._guardian_election_public_keys)

    def generate_election_partial_key_backups(
        self, encrypt: AuxiliaryEncrypt = rsa_encrypt
    ) -> bool:
        """
        Generate all election partial key backups based on existing public keys
        :param encrypt: Encryption function using auxiliary key
        """
        if not self.all_auxiliary_public_keys_received():
            log_warning(
                f"guardian; {self.object_id} could not generate election partial key backups: missing auxiliary keys"
            )
            return False
        for auxiliary_key in self._guardian_auxiliary_public_keys.values():
            backup = generate_election_partial_key_backup(
                self.object_id, self._election_keys.polynomial, auxiliary_key, encrypt
            )
            if backup is None:
                log_warning(
                    f"guardian; {self.object_id} could not generate election partial key backups: failed to encrypt"
                )
                return False
            self._backups_to_share.set(auxiliary_key.owner_id, backup)

        return True

    # Election Partial Key Backup
    def share_election_partial_key_backup(
        self, designated_id: GUARDIAN_ID
    ) -> Optional[ElectionPartialKeyBackup]:
        """
        Share election partial key backup with another guardian
        :param designated_id: Designated guardian
        :return: Election partial key backup or None
        """
        return self._backups_to_share.get(designated_id)

    def save_election_partial_key_backup(
        self, backup: ElectionPartialKeyBackup
    ) -> None:
        """
        Save election partial key backup from another guardian
        :param backup: Election partial key backup
        """
        self._guardian_election_partial_key_backups.set(backup.owner_id, backup)

    def all_election_partial_key_backups_received(self) -> bool:
        """
        True if all election partial key backups have been received.
        :return: All election partial key backups received
        """
        return (
            len(self._guardian_election_partial_key_backups)
            == self.ceremony_details.number_of_guardians - 1
        )

    # Verification
    def verify_election_partial_key_backup(
        self, guardian_id: GUARDIAN_ID, decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Optional[ElectionPartialKeyVerification]:
        """
        Verify election partial key backup value is in polynomial
        :param guardian_id: Owner of backup to verify
        :param decrypt: 
        :return: Election partial key verification or None
        """
        backup = self._guardian_election_partial_key_backups.get(guardian_id)
        if backup is None:
            return None
        return verify_election_partial_key_backup(
            self.object_id, backup, self._auxiliary_keys, decrypt
        )

    def publish_election_backup_challenge(
        self, guardian_id: GUARDIAN_ID
    ) -> Optional[ElectionPartialKeyChallenge]:
        """
        Publish election backup challenge of election partial key verification
        :param guardian_id: Owner of election key 
        :return: Election partial key challenge or None
        """
        backup_in_question = self._backups_to_share.get(guardian_id)
        if backup_in_question is None:
            return None
        return generate_election_partial_key_challenge(
            backup_in_question, self._election_keys.polynomial
        )

    def verify_election_partial_key_challenge(
        self, challenge: ElectionPartialKeyChallenge
    ) -> ElectionPartialKeyVerification:
        """
        Verify challenge of previous verification of election partial key
        :param challenge: Election partial key challenge
        :return: Election partial key verification 
        """
        return verify_election_partial_key_challenge(self.object_id, challenge)

    def save_election_partial_key_verification(
        self, verification: ElectionPartialKeyVerification
    ) -> None:
        """
        Save election partial key verification from another guardian
        :param verification: Election partial key verification
        """
        self._guardian_election_partial_key_verifications.set(
            verification.designated_id, verification
        )

    def all_election_partial_key_backups_verified(self) -> bool:
        """
        True if all election partial key backups have been verified.
        :return: All election partial key backups verified
        """
        required = self.ceremony_details.number_of_guardians - 1
        if len(self._guardian_election_partial_key_verifications) != required:
            return False
        for verified in self._guardian_election_partial_key_verifications.values():
            if not verified:
                return False
        return True

    # Joint Key
    def publish_joint_key(self) -> Optional[ElectionJointKey]:
        """
        Creates a joint election key from the public keys of all guardians
        :return: Optional joint key for election
        """
        if not self.all_election_public_keys_received():
            return None
        if not self.all_election_partial_key_backups_verified():
            return None
        return combine_election_public_keys(self._guardian_election_public_keys)

    def partially_decrypt(
        self,
        elgamal: ElGamalCiphertext,
        extended_base_hash: ElementModQ,
        nonce_seed: ElementModQ = None,
    ) -> Tuple[ElementModP, ChaumPedersenProof]:
        """
        Compute a partial decryption of an elgamal encryption

        :param elgamal: the `ElGamalCiphertext` that will be partially decrypted
        :param extended_base_hash: the extended base hash of the election that 
                                   was used to generate t he ElGamal Ciphertext
        :param nonce_seed: an optional value used to generate the `ChaumPedersenProof`
                           if no value is provided, a random number will be used.
        :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
        """
        if nonce_seed is None:
            nonce_seed = rand_q()

        # TODO: ISSUE #47: Decrypt the election secret key

        # 𝑀_i = 𝐴^𝑠𝑖 mod 𝑝
        partial_decryption = elgamal.partial_decrypt(
            self._election_keys.key_pair.secret_key
        )

        # 𝑀_i = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
        proof = make_chaum_pedersen(
            message=elgamal,
            s=self._election_keys.key_pair.secret_key,
            m=partial_decryption,
            seed=nonce_seed,
            hash_header=extended_base_hash,
        )

        return (partial_decryption, proof)

    def compensate_decrypt(
        self,
        missing_guardian_id: str,
        elgamal: ElGamalCiphertext,
        extended_base_hash: ElementModQ,
        nonce_seed: ElementModQ = None,
        decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Optional[Tuple[ElementModP, ChaumPedersenProof]]:
        """
        Compute a compensated partial decryption of an elgamal encryption 
        on behalf of the missing guardian

        :param missing_guardian_id: the guardian 
        :param elgamal: the `ElGamalCiphertext` that will be partially decrypted
        :param extended_base_hash: the extended base hash of the election that 
                                   was used to generate t he ElGamal Ciphertext
        :param nonce_seed: an optional value used to generate the `ChaumPedersenProof`
                           if no value is provided, a random number will be used.
        :param decrypt: an `AuxiliaryDecrypt` function to decrypt the missing guardina private key backup
        :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
        """
        if nonce_seed is None:
            nonce_seed = rand_q()

        backup = self._guardian_election_partial_key_backups.get(missing_guardian_id)
        if backup is None:
            log_warning(
                f"compensate decrypt guardian {self.object_id} missing backup for {missing_guardian_id}"
            )
            return None

        decrypted_value = decrypt(
            backup.encrypted_value, self._auxiliary_keys.secret_key
        )
        if decrypted_value is None:
            log_warning(
                f"compensate decrypt guardian {self.object_id} failed decryption for {missing_guardian_id}"
            )
            return None
        partial_secret_key = get_optional(int_to_q(int(decrypted_value)))

        # 𝑀_{𝑖,l} = 𝐴^P𝑖_{l}
        partial_decryption = elgamal.partial_decrypt(partial_secret_key)

        # 𝑀_{𝑖,l} = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
        proof = make_chaum_pedersen(
            message=elgamal,
            s=partial_secret_key,
            m=partial_decryption,
            seed=nonce_seed,
            hash_header=extended_base_hash,
        )

        return (partial_decryption, proof)

    def recovery_public_key_for(
        self, missing_guardian_id: GUARDIAN_ID
    ) -> Optional[ElementModP]:
        """
        Compute the recovery public key for a given guardian
        """
        backup = self._guardian_election_partial_key_backups.get(missing_guardian_id)
        if backup is None:
            log_warning(
                f"compensate decrypt guardian {self.object_id} missing backup for {missing_guardian_id}"
            )
            return None

        # compute the recovery public key,
        # corresponding to the secret share Pi(l)
        # K_ij^(l^j) for j in 0..k-1.  K_ij is coefficients[j].public_key
        pub_key = ONE_MOD_P
        for index, commitment in enumerate(backup.coefficient_commitments):
            exponent = pow_q(self.sequence_order, index)
            pub_key = mult_p(pub_key, pow_p(commitment, exponent))

        return pub_key
