from dataclasses import dataclass
from typing import List, Optional, NamedTuple

from .auxiliary import (
    AuxiliaryKeyPair,
    AuxiliaryDecrypt,
    AuxiliaryEncrypt,
    AuxiliaryPublicKey,
)
from .data_store import DataStore
from .election_polynomial import (
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
from .group import int_to_q, rand_q, ElementModP, ElementModQ
from .rsa import rsa_keypair, rsa_decrypt, rsa_encrypt
from .schnorr import SchnorrProof, make_schnorr_proof
from .serializable import Serializable
from .types import GUARDIAN_ID
from .utils import get_optional

ElectionJointKey = ElementModP


class CeremonyDetails(NamedTuple):
    """
    Details of key ceremony
    """

    number_of_guardians: int
    quorum: int


class ElectionKeyPair(NamedTuple):
    """A tuple of election key pair, proof and polynomial"""

    key_pair: ElGamalKeyPair
    proof: SchnorrProof
    polynomial: ElectionPolynomial


class ElectionPublicKey(NamedTuple):
    """A tuple of election public key and owner information"""

    owner_id: GUARDIAN_ID
    proof: SchnorrProof
    key: ElementModP


class PublicKeySet(NamedTuple):
    """Public key set of auxiliary and election keys and owner information"""

    owner_id: GUARDIAN_ID
    sequence_order: int
    auxiliary_public_key: str
    election_public_key: ElementModP
    election_public_key_proof: SchnorrProof


class GuardianPair(NamedTuple):
    """Pair of guardians involved in sharing"""

    owner_id: GUARDIAN_ID
    designated_id: GUARDIAN_ID


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

    coefficient_commitments: List[ElementModP]
    """
    The public keys `K_ij`generated from the election polynomial coefficients
    """

    coefficient_proofs: List[SchnorrProof]
    """
    the proofs of posession of the private keys for the election polynomial secret coefficients
    """


@dataclass
class CoefficientValidationSet(Serializable):
    """Set of validation pieces for election key coefficients"""

    owner_id: GUARDIAN_ID
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


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
    """
    The sequence order of the designated guardian
    """

    value: int
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


def generate_elgamal_auxiliary_key_pair() -> AuxiliaryKeyPair:
    """
    Generate auxiliary key pair using elgamal
    :return: Auxiliary key pair
    """
    elgamal_key_pair = elgamal_keypair_random()
    return AuxiliaryKeyPair(
        str(elgamal_key_pair.secret_key.to_int()),
        str(elgamal_key_pair.public_key.to_int()),
    )


def generate_rsa_auxiliary_key_pair() -> AuxiliaryKeyPair:
    """
    Generate auxiliary key pair using RSA
    :return: Auxiliary key pair
    """
    rsa_key_pair = rsa_keypair()
    return AuxiliaryKeyPair(rsa_key_pair.private_key, rsa_key_pair.public_key)


def generate_election_key_pair(
    quorum: int, nonce: ElementModQ = None
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
    proof = make_schnorr_proof(key_pair, rand_q())
    return ElectionKeyPair(key_pair, proof, polynomial)


def generate_election_partial_key_backup(
    owner_id: GUARDIAN_ID,
    polynomial: ElectionPolynomial,
    auxiliary_public_key: AuxiliaryPublicKey,
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
        auxiliary_public_key.sequence_order, polynomial
    )
    encrypted_value = encrypt(str(value.to_int()), auxiliary_public_key.key)
    if encrypted_value is None:
        return None
    return ElectionPartialKeyBackup(
        owner_id,
        auxiliary_public_key.owner_id,
        auxiliary_public_key.sequence_order,
        encrypted_value,
        polynomial.coefficient_commitments,
        polynomial.coefficient_proofs,
    )


def get_coefficient_validation_set(
    owner_id: GUARDIAN_ID, polynomial: ElectionPolynomial,
) -> CoefficientValidationSet:
    """Get coefficient validation set from polynomial"""
    return CoefficientValidationSet(
        owner_id, polynomial.coefficient_commitments, polynomial.coefficient_proofs,
    )


def get_coefficient_validation_set_from_backup(
    backup: ElectionPartialKeyBackup,
) -> CoefficientValidationSet:
    """Get coefficient validation set from a election partial key backup"""
    return CoefficientValidationSet(
        backup.owner_id, backup.coefficient_commitments, backup.coefficient_proofs,
    )


def verify_election_partial_key_backup(
    verifier_id: GUARDIAN_ID,
    backup: ElectionPartialKeyBackup,
    auxiliary_key_pair: AuxiliaryKeyPair,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
) -> ElectionPartialKeyVerification:
    """
    Verify election partial key backup contain point on owners polynomial
    :param verifier_id: Verifier of the partial key backup
    :param backup: Election partial key backup
    :param auxiliary_key_pair: Auxiliary key pair
    :param decrypt: Decryption function using auxiliary key
    """

    decrypted_value = decrypt(backup.encrypted_value, auxiliary_key_pair.secret_key)
    if decrypted_value is None:
        return ElectionPartialKeyVerification(
            backup.owner_id, backup.designated_id, verifier_id, False
        )
    value = get_optional(int_to_q(int(decrypted_value)))
    return ElectionPartialKeyVerification(
        backup.owner_id,
        backup.designated_id,
        verifier_id,
        verify_polynomial_coordinate(
            value, backup.designated_sequence_order, backup.coefficient_commitments
        ),
    )


def generate_election_partial_key_challenge(
    backup: ElectionPartialKeyBackup, polynomial: ElectionPolynomial,
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
        compute_polynomial_coordinate(
            backup.designated_sequence_order, polynomial
        ).to_int(),
        backup.coefficient_commitments,
        backup.coefficient_proofs,
    )


def verify_election_partial_key_challenge(
    verifier_id: GUARDIAN_ID, challenge: ElectionPartialKeyChallenge
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
            get_optional(int_to_q(challenge.value)),
            challenge.designated_sequence_order,
            challenge.coefficient_commitments,
        ),
    )


def combine_election_public_keys(
    election_public_keys: DataStore[GUARDIAN_ID, ElectionPublicKey]
) -> ElectionJointKey:
    """
    Creates a joint election key from the public keys of all guardians
    :return: Joint key for election
    """
    public_keys = map(lambda public_key: public_key.key, election_public_keys.values())

    return elgamal_combine_public_keys(public_keys)
