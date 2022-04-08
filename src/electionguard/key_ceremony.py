from dataclasses import dataclass
from typing import List

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
    elgamal_combine_public_keys,
)
from .group import ElementModQ
from .hash import hash_elems
from .schnorr import SchnorrProof
from .type import (
    GuardianId,
    VerifierId,
)
from .utils import get_optional


@dataclass
class GuardianPublicKey:
    """A record of the public info of guardian including election public key and owner information"""

    owner_id: GuardianId
    """Unique identifier of the guardian"""

    sequence_order: int
    """
    Unique sequence order of the guardian indicating the order
    in which the guardian should be processed
    """

    public_key: ElGamalPublicKey
    """
    The public key for the guardian
    Note: This is the same as the first coefficient commitment
    """

    commitments: List[PublicCommitment]
    """
    Commitment for each coeffficient of the guardians secret polynomial.
    First commitment is and should be identical to public_key.
    """

    proofs: List[SchnorrProof]
    """
    Proofs for each commitment for each coeffficient of the guardians secret polynomial.
    First proof is the proof for the public_key.
    """


@dataclass
class GuardianKeyPair:
    """A tuple of a guardian key pair, proof and polynomial"""

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

    def share(self) -> GuardianPublicKey:
        """Share the election public key and associated data"""
        return GuardianPublicKey(
            self.owner_id,
            self.sequence_order,
            self.key_pair.public_key,
            self.polynomial.get_commitments(),
            self.polynomial.get_proofs(),
        )


@dataclass
class ElectionKey:
    """
    The public Election Key used for encrypting ballots in the election.
    This is a joint key of all the guardians public keys.
    """

    public_key: ElGamalPublicKey
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

    coordinate: ElementModQ
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

    coordinate: ElementModQ
    commitments: List[PublicCommitment]
    proofs: List[SchnorrProof]


def generate_guardian_key_pair(
    guardian_id: str, sequence_order: int, quorum: int, nonce: ElementModQ = None
) -> GuardianKeyPair:
    """
    Generate election key pair, proof, and polynomial
    :param quorum: Quorum of guardians needed to decrypt
    :return: Election key pair
    """
    polynomial = generate_polynomial(quorum, nonce)
    key_pair = ElGamalKeyPair(
        polynomial.coefficients[0].value, polynomial.coefficients[0].commitment
    )
    return GuardianKeyPair(guardian_id, sequence_order, key_pair, polynomial)


def generate_election_partial_key_backup(
    owner_id: GuardianId,
    polynomial: ElectionPolynomial,
    designated_guardian_key: GuardianPublicKey,
) -> ElectionPartialKeyBackup:
    """
    Generate election partial key backup for sharing
    :param owner_id: Owner of election key
    :param polynomial: The owner's Election polynomial
    :return: Election partial key backup
    """
    value = compute_polynomial_coordinate(
        designated_guardian_key.sequence_order, polynomial
    )
    return ElectionPartialKeyBackup(
        owner_id,
        designated_guardian_key.owner_id,
        designated_guardian_key.sequence_order,
        value,
    )


def verify_election_partial_key_backup(
    verifier_id: str,
    backup: ElectionPartialKeyBackup,
    election_public_key: GuardianPublicKey,
) -> ElectionPartialKeyVerification:
    """
    Verify election partial key backup contain point on owners polynomial
    :param verifier_id: Verifier of the partial key backup
    :param backup: Other guardian's election partial key backup
    :param election_public_key: Other guardian's election public key
    """

    coordinate = backup.coordinate
    return ElectionPartialKeyVerification(
        backup.owner_id,
        backup.designated_id,
        verifier_id,
        verify_polynomial_coordinate(
            coordinate,
            backup.designated_sequence_order,
            election_public_key.commitments,
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
            challenge.coordinate,
            challenge.designated_sequence_order,
            challenge.commitments,
        ),
    )


def create_election_key(
    guardian_public_keys: List[GuardianPublicKey],
) -> ElectionKey:
    """
    Creates a joint election key from the public keys of all guardians
    :param election_public_keys: all public keys of the guardians
    :return: ElectionJointKey for election
    """
    public_keys = [set.public_key for set in guardian_public_keys]
    commitments = [
        commitment for set in guardian_public_keys for commitment in set.commitments
    ]

    return ElectionKey(
        public_key=elgamal_combine_public_keys(public_keys),
        commitment_hash=get_optional(
            hash_elems(commitments)
        ),  # H(K 1,0 , K 2,0 ... , K n,0 )
    )
