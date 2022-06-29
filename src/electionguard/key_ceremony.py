from dataclasses import dataclass
from typing import List, Type, TypeVar

from .serialize import padded_decode, padded_encode
from .election_polynomial import (
    PublicCommitment,
    compute_polynomial_coordinate,
    ElectionPolynomial,
    generate_polynomial,
    verify_polynomial_coordinate,
)
from .elgamal import (
    ElGamalKeyPair,
    ElGamalPublicKey,
    HashedElGamalCiphertext,
    elgamal_combine_public_keys,
    hashed_elgamal_encrypt,
)
from .group import ElementModQ, rand_q
from .hash import hash_elems
from .schnorr import SchnorrProof
from .type import (
    GuardianId,
    VerifierId,
)
from .utils import get_optional


@dataclass
class ElectionPublicKey:
    """A tuple of election public key and owner information"""

    owner_id: GuardianId
    """
    The id of the owner guardian
    """

    sequence_order: int
    """
    The sequence order of the owner guardian
    """

    key: ElGamalPublicKey
    """
    The election public for the guardian
    Note: This is the same as the first coefficient commitment
    """

    coefficient_commitments: List[PublicCommitment]
    """
    The commitments for the coefficients in the secret polynomial
    """

    coefficient_proofs: List[SchnorrProof]
    """
    The proofs for the coefficients in the secret polynomial
    """


@dataclass
class ElectionKeyPair:
    """A tuple of election key pair, proof and polynomial"""

    owner_id: GuardianId
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
            self.polynomial.get_commitments(),
            self.polynomial.get_proofs(),
        )


@dataclass
class ElectionJointKey:
    """
    The Election joint key
    """

    joint_public_key: ElGamalPublicKey
    """
    The product of the guardian public keys
    K = ∏ ni=1 Ki mod p.
    """
    commitment_hash: ElementModQ
    """
    The hash of the commitments that the guardians make to each other
    H = H(K 1,0 , K 2,0 ... , K n,0 )
    """


@dataclass
class ElectionPartialKeyBackup:
    """Election partial key backup used for key sharing"""

    owner_id: GuardianId
    """
    The Id of the guardian that generated this backup
    """

    designated_id: GuardianId
    """
    The Id of the guardian to receive this backup
    """

    designated_sequence_order: int
    """
    The sequence order of the designated guardian
    """

    encrypted_coordinate: HashedElGamalCiphertext
    """
    The coordinate corresponding to a secret election polynomial
    """


@dataclass
class CeremonyDetails:
    """Details of key ceremony"""

    number_of_guardians: int
    quorum: int


@dataclass
class ElectionPartialKeyVerification:
    """Verification of election partial key used in key sharing"""

    owner_id: GuardianId
    designated_id: GuardianId
    verifier_id: GuardianId
    verified: bool


@dataclass
class ElectionPartialKeyChallenge:
    """Challenge of election partial key used in key sharing"""

    owner_id: GuardianId
    designated_id: GuardianId
    designated_sequence_order: int

    value: ElementModQ
    coefficient_commitments: List[PublicCommitment]
    coefficient_proofs: List[SchnorrProof]


_T = TypeVar("_T", bound="CoordinateData")


@dataclass
class CoordinateData:
    """A coordinate from a PartialKeyBackup that can be serialized and deserialized for encryption/decryption"""

    coordinate: ElementModQ

    @classmethod
    def from_bytes(cls: Type[_T], data: bytes) -> _T:
        return padded_decode(cls, data)

    def to_bytes(self) -> bytes:
        return padded_encode(self)


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
        polynomial.coefficients[0].value, polynomial.coefficients[0].commitment
    )
    return ElectionKeyPair(guardian_id, sequence_order, key_pair, polynomial)


def generate_election_partial_key_backup(
    sender_guardian_id: GuardianId,
    sender_guardian_polynomial: ElectionPolynomial,
    receiver_guardian_public_key: ElectionPublicKey,
) -> ElectionPartialKeyBackup:
    """
    Generate election partial key backup for sharing
    :param sender_guardian_id: Owner of election key
    :param sender_guardian_polynomial: The owner's Election polynomial
    :param receiver_guardian_public_key: The receiving guardian's public key
    :return: Election partial key backup
    """
    coordinate = compute_polynomial_coordinate(
        receiver_guardian_public_key.sequence_order, sender_guardian_polynomial
    )
    coordinate_data = CoordinateData(coordinate)
    nonce = rand_q()
    seed = get_backup_seed(
        receiver_guardian_public_key.owner_id,
        receiver_guardian_public_key.sequence_order,
    )
    encrypted_coordinate = hashed_elgamal_encrypt(
        coordinate_data.to_bytes(),
        nonce,
        receiver_guardian_public_key.key,
        seed,
    )
    return ElectionPartialKeyBackup(
        sender_guardian_id,
        receiver_guardian_public_key.owner_id,
        receiver_guardian_public_key.sequence_order,
        encrypted_coordinate,
    )


def get_backup_seed(receiver_guardian_id: str, sequence_order: int) -> ElementModQ:
    return hash_elems(receiver_guardian_id, sequence_order)


def verify_election_partial_key_backup(
    receiver_guardian_id: str,
    sender_guardian_backup: ElectionPartialKeyBackup,
    sender_guardian_public_key: ElectionPublicKey,
    receiver_guardian_keys: ElectionKeyPair,
) -> ElectionPartialKeyVerification:
    """
    Verify election partial key backup contain point on owners polynomial
    :param receiver_guardian_id: Receiving guardian's identifier
    :param sender_guardian_backup: Sender guardian's election partial key backup
    :param sender_guardian_public_key: Sender guardian's election public key
    :param receiver_guardian_keys: Receiving guardian's key pair
    """

    encryption_seed = get_backup_seed(
        receiver_guardian_id,
        sender_guardian_backup.designated_sequence_order,
    )

    secret_key = receiver_guardian_keys.key_pair.secret_key
    bytes_optional = sender_guardian_backup.encrypted_coordinate.decrypt(
        secret_key, encryption_seed
    )
    coordinate_data: CoordinateData = CoordinateData.from_bytes(
        get_optional(bytes_optional)
    )
    verified = verify_polynomial_coordinate(
        coordinate_data.coordinate,
        sender_guardian_backup.designated_sequence_order,
        sender_guardian_public_key.coefficient_commitments,
    )
    return ElectionPartialKeyVerification(
        sender_guardian_backup.owner_id,
        sender_guardian_backup.designated_id,
        receiver_guardian_id,
        verified,
    )


def generate_election_partial_key_challenge(
    backup: ElectionPartialKeyBackup,
    polynomial: ElectionPolynomial,
) -> ElectionPartialKeyChallenge:
    """
    Generate challenge to a previous verification of a partial key backup
    :param backup: Election partial key backup in question
    :param polynomial: Polynomial to regenerate point
    :return: Election partial key verification
    """
    return ElectionPartialKeyChallenge(
        backup.owner_id,
        backup.designated_id,
        backup.designated_sequence_order,
        compute_polynomial_coordinate(backup.designated_sequence_order, polynomial),
        polynomial.get_commitments(),
        polynomial.get_proofs(),
    )


def verify_election_partial_key_challenge(
    verifier_id: VerifierId, challenge: ElectionPartialKeyChallenge
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
