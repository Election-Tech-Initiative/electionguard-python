from typing import (
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    NamedTuple,
    Optional,
    TypeVar,
)

from .election_polynomial import (
    compute_polynomial_value,
    ElectionPolynomial,
    generate_polynomial,
    verify_polynomial_value,
)
from .elgamal import (
    ElGamalKeyPair,
    elgamal_combine_public_keys,
    elgamal_keypair_random,
)
from .group import (
    int_to_q_unchecked,
    rand_q,
    ElementModP,
)
from .schnorr import SchnorrProof, make_schnorr_proof


class CeremonyDetails(NamedTuple):
    """
    Details of key ceremony
    """

    number_of_guardians: int
    quorum: int


GuardianId = str


class AuxiliaryKeyPair(NamedTuple):
    """A tuple of a secret key and public key."""

    secret_key: str
    """The secret or private key"""
    public_key: str


class AuxiliaryPublicKey(NamedTuple):
    owner_id: GuardianId
    sequence_order: int
    key: str


AuxiliaryEncrypt = Callable[[str, AuxiliaryPublicKey], str]

# FIX_ME Default Auxiliary Encrypt is temporary placeholder
default_auxiliary_encrypt = lambda unencrypted, key: unencrypted

AuxiliaryDecrypt = Callable[[str, AuxiliaryKeyPair], str]

# FIX_ME Default Auxiliary Decrypt is temporary placeholder
default_auxiliary_decrypt = lambda encrypted, key_pair: encrypted


class ElectionKeyPair(NamedTuple):
    key_pair: ElGamalKeyPair
    proof: SchnorrProof
    polynomial: ElectionPolynomial


class ElectionPublicKey(NamedTuple):
    owner_id: GuardianId
    proof: SchnorrProof
    key: ElementModP


class PublicKeySet(NamedTuple):
    owner_id: GuardianId
    sequence_order: int
    auxiliary_public_key: str
    election_public_key: ElementModP
    election_public_key_proof: SchnorrProof


class GuardianPair(NamedTuple):
    owner_id: GuardianId
    designated_id: GuardianId


class ElectionPartialKeyBackup(NamedTuple):
    owner_id: GuardianId
    designated_id: GuardianId
    designated_sequence_order: int

    encrypted_value: str
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


class ElectionPartialKeyVerification(NamedTuple):
    owner_id: GuardianId
    designated_id: GuardianId
    verifier_id: GuardianId
    verified: bool


class ElectionPartialKeyChallenge(NamedTuple):
    owner_id: GuardianId
    designated_id: GuardianId
    designated_sequence_order: int

    value: int
    coefficient_commitments: List[ElementModP]
    coefficient_proofs: List[SchnorrProof]


ElectionJointKey = ElementModP

T = TypeVar("T")
U = TypeVar("U")


class GuardianDataStore(Generic[T, U]):
    _store: Dict[T, U]

    def __init__(self) -> None:
        self._store = {}

    def set(self, key: T, value: U) -> None:
        self._store[key] = value

    def get(self, key: T) -> Optional[U]:
        return self._store.get(key)

    def length(self) -> int:
        return len(self._store)

    def values(self) -> Iterable[U]:
        return self._store.values()

    def clear(self) -> None:
        self._store.clear()


def generate_elgamal_auxiliary_key_pair() -> AuxiliaryKeyPair:
    elgamal_key_pair = elgamal_keypair_random()
    return AuxiliaryKeyPair(
        str(elgamal_key_pair.secret_key.to_int()),
        str(elgamal_key_pair.public_key.to_int()),
    )


def generate_election_key_pair(quorum: int) -> ElectionKeyPair:
    polynomial = generate_polynomial(quorum)
    key_pair = ElGamalKeyPair(
        polynomial.coefficients[0], polynomial.coefficient_commitments[0]
    )
    proof = make_schnorr_proof(key_pair, rand_q())
    return ElectionKeyPair(key_pair, proof, polynomial)


def generate_election_partial_key_backup(
    owner_id: GuardianId,
    polynomial: ElectionPolynomial,
    auxiliary_public_key: AuxiliaryPublicKey,
    encrypt: AuxiliaryEncrypt = default_auxiliary_encrypt,
) -> ElectionPartialKeyBackup:
    value = compute_polynomial_value(auxiliary_public_key.sequence_order, polynomial)
    encrypted_value = encrypt(str(value.to_int()), auxiliary_public_key)
    return ElectionPartialKeyBackup(
        owner_id,
        auxiliary_public_key.owner_id,
        auxiliary_public_key.sequence_order,
        encrypted_value,
        polynomial.coefficient_commitments,
        polynomial.coefficient_proofs,
    )


def verify_election_partial_key_backup(
    verifier_id: GuardianId,
    backup: ElectionPartialKeyBackup,
    auxiliary_key_pair: AuxiliaryKeyPair,
    decrypt: AuxiliaryDecrypt = default_auxiliary_decrypt,
) -> ElectionPartialKeyVerification:
    decrypted_value = decrypt(backup.encrypted_value, auxiliary_key_pair)
    value = int_to_q_unchecked(int(decrypted_value))

    return ElectionPartialKeyVerification(
        backup.owner_id,
        backup.designated_id,
        verifier_id,
        verify_polynomial_value(
            value, backup.designated_sequence_order, backup.coefficient_commitments
        ),
    )


def generate_election_partial_key_challenge(
    backup: ElectionPartialKeyBackup, polynomial: ElectionPolynomial,
) -> ElectionPartialKeyChallenge:
    return ElectionPartialKeyChallenge(
        backup.owner_id,
        backup.designated_id,
        backup.designated_sequence_order,
        compute_polynomial_value(backup.designated_sequence_order, polynomial).to_int(),
        backup.coefficient_commitments,
        backup.coefficient_proofs,
    )


def verify_election_partial_key_challenge(
    verifier_id: GuardianId, challenge: ElectionPartialKeyChallenge
) -> ElectionPartialKeyVerification:
    return ElectionPartialKeyVerification(
        challenge.owner_id,
        challenge.designated_id,
        verifier_id,
        verify_polynomial_value(
            int_to_q_unchecked(challenge.value),
            challenge.designated_sequence_order,
            challenge.coefficient_commitments,
        ),
    )


def combine_election_public_keys(
    election_public_keys: GuardianDataStore[GuardianId, ElectionPublicKey]
) -> ElectionJointKey:
    # FIXME Lambda or map may not be capable of being transliterated. Consider alternative.
    public_keys = map(lambda public_key: public_key.key, election_public_keys.values())

    return elgamal_combine_public_keys(public_keys)
