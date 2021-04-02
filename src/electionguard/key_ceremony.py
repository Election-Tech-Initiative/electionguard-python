from typing import List, Optional, NamedTuple

from .auxiliary import (
    AuxiliaryDecrypt,
    AuxiliaryEncrypt,
    AuxiliaryKeyPair,
    AuxiliaryPublicKey,
)
from .election_polynomial import (
    PUBLIC_COMMITMENT,
    compute_polynomial_coordinate,
    ElectionPolynomial,
    generate_polynomial,
    verify_polynomial_coordinate,
)
from .elgamal import (
    ElGamalKeyPair,
    elgamal_combine_public_keys,
    elgamal_keypair_random,
)
from .group import hex_to_q, ElementModP, ElementModQ
from .hash import hash_elems
from .rsa import rsa_keypair, rsa_decrypt, rsa_encrypt
from .schnorr import SchnorrProof
from .types import GUARDIAN_ID
from .utils import get_optional

ELECTION_PUBLIC_KEY = ElementModP
ELECTION_JOINT_PUBLIC_KEY = ElementModP
VERIFIER_ID = str


class ElectionPublicKey(NamedTuple):
    """A tuple of election public key and owner information"""

    owner_id: GUARDIAN_ID
    """
    The id of the owner guardian
    """

    sequence_order: int
    """
    The sequence order of the owner guardian
    """

    key: ELECTION_PUBLIC_KEY
    """
    The election public for the guardian
    Note: This is the same as the first coefficient commitment
    """

    coefficient_commitments: List[PUBLIC_COMMITMENT]
    """
    The commitments for the coefficients in the secret polynomial
    """

    coefficient_proofs: List[SchnorrProof]
    """
    The proofs for the coefficients in the secret polynomial
    """


class ElectionKeyPair(NamedTuple):
    """A tuple of election key pair, proof and polynomial"""

    owner_id: GUARDIAN_ID
    """
    The id of the owner guardian
    """

    sequence_order: int
    """
    The sequence order of the owner guardian
    """

    key_pair: ElGamalKeyPair
    """
    The pair of public and private election keys for the guardian
    """

    polynomial: ElectionPolynomial
    """
    The secret polynomial for the guardian
    """

    def share(self) -> ElectionPublicKey:
        """Share the election public key and associated data"""
        return ElectionPublicKey(
            self.owner_id,
            self.sequence_order,
            self.key_pair.public_key,
            self.polynomial.coefficient_commitments,
            self.polynomial.coefficient_proofs,
        )


class ElectionJointKey(NamedTuple):
    """
    The Election joint key
    """

    joint_public_key: ELECTION_JOINT_PUBLIC_KEY
    """
    The product of the guardian public keys
    K = ∏ ni=1 Ki mod p.
    """
    commitment_hash: ElementModQ
    """
    The hash of the commitments that the guardians make to each other
    H = H(K 1,0 , K 2,0 ... , K n,0 )
    """


class ElectionPartialKeyBackup(NamedTuple):
    """Election partial key backup used for key sharing"""

    owner_id: GUARDIAN_ID
    """
    The Id of the guardian that generated this backup
    """

    designated_id: GUARDIAN_ID
    """
    The Id of the guardian to receive this backup
    """

    designated_sequence_order: int
    """
    The sequence order of the designated guardian
    """

    encrypted_value: str
    """
    The encrypted coordinate corresponding to a secret election polynomial
    """


class CeremonyDetails(NamedTuple):
    """
    Details of key ceremony
    """

    number_of_guardians: int
    quorum: int


class PublicKeySet(NamedTuple):
    """A convenience set of public auxiliary and election keys"""

    election: ElectionPublicKey
    auxiliary: AuxiliaryPublicKey


class ElectionPartialKeyVerification(NamedTuple):
    """Verification of election partial key used in key sharing"""

    owner_id: GUARDIAN_ID
    designated_id: GUARDIAN_ID
    verifier_id: GUARDIAN_ID
    verified: bool


class ElectionPartialKeyChallenge(NamedTuple):
    """Challenge of election partial key used in key sharing"""

    owner_id: GUARDIAN_ID
    designated_id: GUARDIAN_ID
    designated_sequence_order: int

    value: ElementModQ
    coefficient_commitments: List[PUBLIC_COMMITMENT]
    coefficient_proofs: List[SchnorrProof]


def generate_elgamal_auxiliary_key_pair(
    owner_id: GUARDIAN_ID, sequence_order: int
) -> AuxiliaryKeyPair:
    """
    Generate auxiliary key pair using elgamal
    :return: Auxiliary key pair
    """
    elgamal_key_pair = elgamal_keypair_random()
    return AuxiliaryKeyPair(
        owner_id,
        sequence_order,
        elgamal_key_pair.secret_key.to_hex(),
        elgamal_key_pair.public_key.to_hex(),
    )


def generate_rsa_auxiliary_key_pair(
    owner_id: GUARDIAN_ID, sequence_order: int
) -> AuxiliaryKeyPair:
    """
    Generate auxiliary key pair using RSA
    :return: Auxiliary key pair
    """
    rsa_key_pair = rsa_keypair()
    return AuxiliaryKeyPair(
        owner_id, sequence_order, rsa_key_pair.private_key, rsa_key_pair.public_key
    )


def generate_election_key_pair(
    guardian_id: str, sequence_order: int, quorum: int, nonce: ElementModQ = None
) -> ElectionKeyPair:
    """
    Generate election key pair, proof, and polynomial
    :param quorum: Quorum of guardians needed to decrypt
    :return: Election key pair
    """
    polynomial = generate_polynomial(quorum, nonce)
    key_pair = ElGamalKeyPair(
        polynomial.coefficients[0], polynomial.coefficient_commitments[0]
    )
    return ElectionKeyPair(guardian_id, sequence_order, key_pair, polynomial)


def generate_election_partial_key_backup(
    owner_id: GUARDIAN_ID,
    polynomial: ElectionPolynomial,
    designated_auxiliary_public_key: AuxiliaryPublicKey,
    encrypt: AuxiliaryEncrypt = rsa_encrypt,
) -> Optional[ElectionPartialKeyBackup]:
    """
    Generate election partial key backup for sharing
    :param owner_id: Owner of election key
    :param polynomial: The owner's Election polynomial
    :param auxiliary_public_key: The Auxiliary public key
    :param encrypt: Function to encrypt using auxiliary key
    :return: Election partial key backup
    """
    value = compute_polynomial_coordinate(
        designated_auxiliary_public_key.sequence_order, polynomial
    )
    encrypted_value = encrypt(value.to_hex(), designated_auxiliary_public_key.key)
    if encrypted_value is None:
        return None
    return ElectionPartialKeyBackup(
        owner_id,
        designated_auxiliary_public_key.owner_id,
        designated_auxiliary_public_key.sequence_order,
        encrypted_value,
    )


def verify_election_partial_key_backup(
    verifier_id: str,
    backup: ElectionPartialKeyBackup,
    election_public_key: ElectionPublicKey,
    verifier_auxiliary_key_pair: AuxiliaryKeyPair,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
) -> ElectionPartialKeyVerification:
    """
    Verify election partial key backup contain point on owners polynomial
    :param verifier_id: Verifier of the partial key backup
    :param backup: Other guardian's election partial key backup
    :param election_public_key: Other guardian's election public key
    :param auxiliary_key_pair: Auxiliary key pair
    :param decrypt: Decryption function using auxiliary key
    """

    decrypted_value = decrypt(
        backup.encrypted_value, verifier_auxiliary_key_pair.secret_key
    )
    if decrypted_value is None:
        return ElectionPartialKeyVerification(
            backup.owner_id, backup.designated_id, verifier_id, False
        )
    value = get_optional(hex_to_q(decrypted_value))
    return ElectionPartialKeyVerification(
        backup.owner_id,
        backup.designated_id,
        verifier_id,
        verify_polynomial_coordinate(
            value,
            backup.designated_sequence_order,
            election_public_key.coefficient_commitments,
        ),
    )


def generate_election_partial_key_challenge(
    backup: ElectionPartialKeyBackup,
    polynomial: ElectionPolynomial,
) -> ElectionPartialKeyChallenge:
    """
    Generate challenge to a previous verification of a partial key backup
    :param backup: Election partial key backup in question
    :param poynomial: Polynomial to regenerate point
    :return: Election partial key verification
    """
    return ElectionPartialKeyChallenge(
        backup.owner_id,
        backup.designated_id,
        backup.designated_sequence_order,
        compute_polynomial_coordinate(backup.designated_sequence_order, polynomial),
        polynomial.coefficient_commitments,
        polynomial.coefficient_proofs,
    )


def verify_election_partial_key_challenge(
    verifier_id: VERIFIER_ID, challenge: ElectionPartialKeyChallenge
) -> ElectionPartialKeyVerification:
    """
    Verify a challenge to a previous verification of a partial key backup
    :param verifier_id: Verifier of the challenge
    :param challenge: Election partial key challenge
    :return: Election partial key verification
    """
    return ElectionPartialKeyVerification(
        challenge.owner_id,
        challenge.designated_id,
        verifier_id,
        verify_polynomial_coordinate(
            challenge.value,
            challenge.designated_sequence_order,
            challenge.coefficient_commitments,
        ),
    )


def combine_election_public_keys(
    election_public_keys: List[ElectionPublicKey],
) -> ElectionJointKey:
    """
    Creates a joint election key from the public keys of all guardians
    :param election_public_keys: all public keys of the guardians
    :return: ElectionJointKey for election
    """
    public_keys = [set.key for set in election_public_keys]
    commitments = [
        commitment
        for set in election_public_keys
        for commitment in set.coefficient_commitments
    ]

    return ElectionJointKey(
        joint_public_key=elgamal_combine_public_keys(public_keys),
        commitment_hash=get_optional(
            hash_elems(commitments)
        ),  # H(K 1,0 , K 2,0 ... , K n,0 )
    )
