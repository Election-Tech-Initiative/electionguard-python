from dataclasses import dataclass, field, replace
from datetime import datetime
from distutils import util
from enum import Enum
from typing import Any, List, Optional, Protocol, runtime_checkable, Sequence

from .chaum_pedersen import (
    ConstantChaumPedersenProof,
    DisjunctiveChaumPedersenProof,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
)
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext, elgamal_add
from .group import add_q, ElementModP, ElementModQ, ZERO_MOD_Q
from .hash import CryptoHashCheckable, hash_elems
from .logs import log_warning
from .tracker import get_rotating_tracker_hash, tracker_hash_to_words
from .utils import to_ticks, flatmap_optional


def _list_eq(
    list1: Sequence[ElectionObjectBase], list2: Sequence[ElectionObjectBase]
) -> bool:
    """
    We want to compare lists of election objects as if they're sets. We fake this by first
    sorting them on their object ids, then using regular list comparison.
    """
    return sorted(list1, key=lambda x: x.object_id) == sorted(
        list2, key=lambda x: x.object_id
    )


@dataclass(eq=True, unsafe_hash=True)
class ExtendedData(object):
    """
    ExtendedData represents any arbitrary data expressible as a string with a length.

    This class is used primarily as a field on a selection to indicate a write-in candidate text value
    """

    value: str
    length: int


@dataclass(unsafe_hash=True)
class PlaintextBallotSelection(ElectionObjectBase):
    """
    A BallotSelection represents an individual selection on a ballot.

    This class accepts a `vote` string field which has no constraints
    in the ElectionGuard Data Specification, but is constrained logically
    in the application to resolve to `True` or `False`.  This implies that the
    data specification supports passing any string that can be represented as
    an integer, however only 0 and 1 is supported for now.

    This class can also be designated as `is_placeholder_selection` which has no
    context to the data specification but is useful for running validity checks internally

    an `extended_data` field exists to support any arbitrary data to be associated
    with the selection.  In practice, this field is the cleartext representation
    of a write-in candidate value.  In the current implementation these values are
    discarded when encrypting.
    """

    vote: str

    is_placeholder_selection: bool = field(default=False)
    """Determines if this is a placeholder selection"""

    # TODO: ISSUE #35: encrypt/decrypt
    extended_data: Optional[ExtendedData] = field(default=None)
    """
    an optional field of arbitrary data, such as the value of a write-in candidate
    """

    def is_valid(self, expected_object_id: str) -> bool:
        """
        Given a PlaintextBallotSelection validates that the object matches an expected object
        and that the plaintext string can resolve to a valid representation
        """

        if self.object_id != expected_object_id:
            log_warning(
                f"invalid object_id: expected({expected_object_id}) actual({self.object_id})"
            )
            return False

        choice = self.to_int()
        if choice < 0 or choice > 1:
            log_warning(f"Currently only supporting choices of 0 or 1: {str(self)}")
            return False

        return True

    def to_int(self) -> int:
        """
        Represent a Truthy string as 1, or if the string is Falsy, 0
        See: https://docs.python.org/3/distutils/apiref.html#distutils.util.strtobool

        :return: an integer 0 or 1 for valid data, or 0 if the data is malformed
        """

        as_bool = False
        try:
            as_bool = util.strtobool(self.vote.lower())
        except ValueError:
            log_warning(
                f"to_int could not convert plaintext: {self.vote.lower()} to bool"
            )

        # TODO: ISSUE #33: If the boolean coercion above fails, support integer votes
        # greater than 1 for cases such as cumulative voting
        as_int = int(as_bool)
        return as_int

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PlaintextBallotSelection)
            and self.object_id == other.object_id
            and self.vote == other.vote
            and self.is_placeholder_selection == other.is_placeholder_selection
            and self.extended_data == other.extended_data
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


@runtime_checkable
class CiphertextSelection(Protocol):
    """
    Encrypted selection
    """

    object_id: str

    description_hash: ElementModQ
    """The SelectionDescription hash"""

    ciphertext: ElGamalCiphertext
    """The encrypted representation of the selection"""


@dataclass(eq=True, unsafe_hash=True)
class CiphertextBallotSelection(
    ElectionObjectBase, CiphertextSelection, CryptoHashCheckable
):
    """
    A CiphertextBallotSelection represents an individual encrypted selection on a ballot.

    This class accepts a `description_hash` and a `ciphertext` as required parameters
    in its constructor.

    When a selection is encrypted, the `description_hash` and `ciphertext` required fields must
    be populated at construction however the `nonce` is also usually provided by convention.

    After construction, the `crypto_hash` field is populated automatically in the `__post_init__` cycle

    A consumer of this object has the option to discard the `nonce` and/or discard the `proof`,
    or keep both values.  
    
    By discarding the `nonce`, the encrypted representation and `proof`
    can only be regenerated if the nonce was derived from the ballot's master nonce.  If the nonce
    used for this selection is truly random, and it is discarded, then the proofs cannot be regenerated.

    By keeping the `nonce`, or deriving the selection nonce from the ballot nonce, an external system can 
    regenerate the proofs on demand.  This is useful for storage or memory constrained systems.

    By keeping the `proof` the nonce is not required fotor verify the encrypted selection.
    """

    description_hash: ElementModQ
    """The SelectionDescription hash"""

    ciphertext: ElGamalCiphertext
    """The encrypted representation of the vote field"""

    crypto_hash: ElementModQ
    """The hash of the encrypted values"""

    is_placeholder_selection: bool = field(default=False)
    """Determines if this is a placeholder selection"""

    nonce: Optional[ElementModQ] = field(default=None)
    """The nonce used to generate the encryption. Sensitive & should be treated as a secret"""

    proof: Optional[DisjunctiveChaumPedersenProof] = field(default=None)
    """The proof that demonstrates the selection is an encryption of 0 or 1, and was encrypted using the `nonce`"""

    # TODO: ISSUE #35: encrypt/decrypt
    extended_data: Optional[ElGamalCiphertext] = field(default=None)
    """encrypted representation of the extended_data field"""

    def is_valid_encryption(
        self,
        seed_hash: ElementModQ,
        elgamal_public_key: ElementModP,
        crypto_extended_base_hash: ElementModQ,
    ) -> bool:
        """
        Given an encrypted BallotSelection, validates the encryption state against a specific seed hash and public key.
        Calling this function expects that the object is in a well-formed encrypted state
        with the elgamal encrypted `message` field populated along with the DisjunctiveChaumPedersenProof `proof` populated.
        the ElementModQ `description_hash` and the ElementModQ `crypto_hash` are also checked. 

        :param seed_hash: the hash of the SelectionDescription, or 
                          whatever `ElementModQ` was used to populate the `description_hash` field.
        :param elgamal_public_key: The election public key
        """

        if seed_hash != self.description_hash:
            log_warning(
                f"mismatching selection hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.description_hash)})"
            )
            return False

        recalculated_crypto_hash = self.crypto_hash_with(seed_hash)
        if self.crypto_hash != recalculated_crypto_hash:
            log_warning(
                f"mismatching crypto hash: {self.object_id} expected({str(recalculated_crypto_hash)}), actual({str(self.crypto_hash)})"
            )
            return False

        if self.proof is None:
            log_warning(f"no proof exists for: {self.object_id}")
            return False

        return self.proof.is_valid(
            self.ciphertext, elgamal_public_key, crypto_extended_base_hash
        )

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted BallotSelection, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `seed_hash` and `message`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.

        In most cases the seed_hash should match the `description_hash`
        """
        return _ciphertext_ballot_selection_crypto_hash_with(
            self.object_id, seed_hash, self.ciphertext
        )


def _ciphertext_ballot_selection_crypto_hash_with(
    object_id: str, seed_hash: ElementModQ, ciphertext: ElGamalCiphertext
) -> ElementModQ:
    return hash_elems(object_id, seed_hash, ciphertext.crypto_hash())


def make_ciphertext_ballot_selection(
    object_id: str,
    description_hash: ElementModQ,
    ciphertext: ElGamalCiphertext,
    elgamal_public_key: ElementModP,
    crypto_extended_base_hash: ElementModQ,
    proof_seed: ElementModQ,
    selection_representation: int,
    is_placeholder_selection: bool = False,
    nonce: Optional[ElementModQ] = None,
    crypto_hash: Optional[ElementModQ] = None,
    proof: Optional[DisjunctiveChaumPedersenProof] = None,
    extended_data: Optional[ElGamalCiphertext] = None,
) -> CiphertextBallotSelection:
    """
    Constructs a `CipherTextBallotSelection` object. Most of the parameters here match up to fields
    in the class, but this helper function will optionally compute a Chaum-Pedersen proof if the
    given nonce isn't `None`. Likewise, if a crypto_hash is not provided, it will be derived from
    the other fields.
    """
    if crypto_hash is None:
        crypto_hash = _ciphertext_ballot_selection_crypto_hash_with(
            object_id, description_hash, ciphertext
        )

    if proof is None:
        proof = flatmap_optional(
            nonce,
            lambda n: make_disjunctive_chaum_pedersen(
                ciphertext,
                n,
                elgamal_public_key,
                crypto_extended_base_hash,
                proof_seed,
                selection_representation,
            ),
        )

    return CiphertextBallotSelection(
        object_id=object_id,
        description_hash=description_hash,
        ciphertext=ciphertext,
        is_placeholder_selection=is_placeholder_selection,
        nonce=nonce,
        crypto_hash=crypto_hash,
        proof=proof,
        extended_data=extended_data,
    )


@dataclass(unsafe_hash=True)
class PlaintextBallotContest(ElectionObjectBase):
    """
    A PlaintextBallotContest represents the selections made by a voter for a specific ContestDescription

    this class can be either a partial or a complete representation of a contest dataset.  Specifically,
    a partial representation must include at a minimum the "affirmative" selections of a contest.
    A complete representation of a ballot must include both affirmative and negative selections of
    the contest, AND the placeholder selections necessary to satisfy the ConstantChaumPedersen proof 
    in the CiphertextBallotContest.

    Typically partial contests are passed into Electionguard for memory constrained systems, 
    while complete contests are passed into ElectionGuard when running encryption on an existing dataset.
    """

    ballot_selections: List[PlaintextBallotSelection] = field(
        default_factory=lambda: []
    )
    """Collection of ballot selections"""

    def is_valid(
        self,
        expected_object_id: str,
        expected_number_selections: int,
        expected_number_elected: int,
        votes_allowed: Optional[int] = None,
    ) -> bool:
        """
        Given a PlaintextBallotContest returns true if the state is representative of the expected values.

        Note: because this class supports partial representations, undervotes are considered a valid state.
        """

        if self.object_id != expected_object_id:
            log_warning(
                f"invalid object_id: expected({expected_object_id}) actual({self.object_id})"
            )
            return False

        if len(self.ballot_selections) > expected_number_selections:
            log_warning(
                f"invalid number_selections: expected({expected_number_selections}) actual({len(self.ballot_selections)})"
            )
            return False

        number_elected = 0
        votes = 0

        # Verify the selections are well-formed
        for selection in self.ballot_selections:
            selection_count = selection.to_int()
            votes += selection_count
            if selection_count >= 1:
                number_elected += 1

        if number_elected > expected_number_elected:
            log_warning(
                f"invalid number_elected: expected({expected_number_elected}) actual({number_elected})"
            )
            return False

        if votes_allowed is not None and votes > votes_allowed:
            log_warning(f"invalid votes: expected({votes_allowed}) actual({votes})")
            return False

        return True

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, PlaintextBallotContest) and _list_eq(
            self.ballot_selections, other.ballot_selections
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


@dataclass(unsafe_hash=True)
class CiphertextBallotContest(ElectionObjectBase, CryptoHashCheckable):
    """
    A CiphertextBallotContest represents the selections made by a voter for a specific ContestDescription

    CiphertextBallotContest can only be a complete representation of a contest dataset.  While
    PlaintextBallotContest supports a partial representation, a CiphertextBallotContest includes all data
    necessary for a verifier to verify the contest.  Specifically, it includes both explicit affirmative 
    and negative selections of the contest, as well as the placeholder selections that satisfy
    the ConstantChaumPedersen proof.

    Similar to `CiphertextBallotSelection` the consuming application can choose to discard or keep both
    the `nonce` and the `proof` in some circumstances.  For deterministic nonce's derived from the 
    master nonce, both values can be regenerated.  If the `nonce` for this contest is completely random,
    then it is required in order to regenerate the proof.
    """

    description_hash: ElementModQ
    """Hash from contestDescription"""

    ballot_selections: List[CiphertextBallotSelection]
    """Collection of ballot selections"""

    crypto_hash: ElementModQ
    """Hash of the encrypted values"""

    nonce: Optional[ElementModQ] = None
    """The nonce used to generate the encryption. Sensitive & should be treated as a secret"""

    proof: Optional[ConstantChaumPedersenProof] = None
    """
    The proof demonstrates the sum of the selections does not exceed the maximum
    available selections for the contest, and that the proof was generated with the nonce
    """

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, CiphertextBallotContest)
            and self.object_id == other.object_id
            and _list_eq(self.ballot_selections, other.ballot_selections)
            and self.description_hash == other.description_hash
            and self.crypto_hash == other.crypto_hash
            and self.nonce == other.nonce
            and self.proof == other.proof
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def aggregate_nonce(self) -> Optional[ElementModQ]:
        """
        :return: an aggregate nonce for the contest composed of the nonces of the selections
        """
        return _ciphertext_ballot_contest_aggregate_nonce(
            self.object_id, self.ballot_selections
        )

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted BallotContest, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `seed_hash` and `ballot_selections`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.

        In most cases, the seed_hash is the description_hash
        """
        return _ciphertext_ballot_context_crypto_hash(
            self.object_id, self.ballot_selections, seed_hash
        )

    def elgamal_accumulate(self) -> ElGamalCiphertext:
        """
        Add the individual ballot_selections `message` fields together, suitable for use
        in a Chaum-Pedersen proof.
        """
        return _ciphertext_ballot_elgamal_accumulate(self.ballot_selections)

    def is_valid_encryption(
        self,
        seed_hash: ElementModQ,
        elgamal_public_key: ElementModP,
        crypto_extended_base_hash: ElementModQ,
    ) -> bool:
        """
        Given an encrypted BallotContest, validates the encryption state against a specific seed hash and public key
        by verifying the accumulated sum of selections match the proof.
        Calling this function expects that the object is in a well-formed encrypted state
        with the `ballot_selections` populated with valid encrypted ballot selections,
        the ElementModQ `description_hash`, the ElementModQ `crypto_hash`, and the ConstantChaumPedersenProof all populated. 
        Specifically, the seed hash in this context is the hash of the ContestDescription, 
        or whatever `ElementModQ` was used to populate the `description_hash` field.
        """
        if seed_hash != self.description_hash:
            log_warning(
                f"mismatching contest hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.description_hash)})"
            )
            return False

        recalculated_crypto_hash = self.crypto_hash_with(seed_hash)
        if self.crypto_hash != recalculated_crypto_hash:
            log_warning(
                f"mismatching crypto hash: {self.object_id} expected({str(recalculated_crypto_hash)}), actual({str(self.crypto_hash)})"
            )
            return False

        # NOTE: this check does not verify the proofs of the individual selections by design.

        if self.proof is None:
            log_warning(f"no proof exists for: {self.object_id}")
            return False

        # Verify the sum of the selections matches the proof
        elgamal_accumulation = self.elgamal_accumulate()
        return self.proof.is_valid(
            elgamal_accumulation, elgamal_public_key, crypto_extended_base_hash
        )


def _ciphertext_ballot_elgamal_accumulate(
    ballot_selections: List[CiphertextBallotSelection],
) -> ElGamalCiphertext:
    return elgamal_add(*[selection.ciphertext for selection in ballot_selections])


def _ciphertext_ballot_context_crypto_hash(
    object_id: str,
    ballot_selections: List[CiphertextBallotSelection],
    seed_hash: ElementModQ,
) -> ElementModQ:
    if len(ballot_selections) == 0:
        log_warning(
            f"mismatching ballot_selections state: {object_id} expected(some), actual(none)"
        )
        return ZERO_MOD_Q

    selection_hashes = [selection.crypto_hash for selection in ballot_selections]

    return hash_elems(object_id, seed_hash, *selection_hashes)


def _ciphertext_ballot_contest_aggregate_nonce(
    object_id: str, ballot_selections: List[CiphertextBallotSelection]
) -> Optional[ElementModQ]:
    selection_nonces: List[ElementModQ] = list()
    for selection in ballot_selections:
        if selection.nonce is None:
            log_warning(
                f"missing nonce values for contest {object_id} cannot calculate aggregate nonce"
            )
            return None
        else:
            selection_nonces.append(selection.nonce)

    return add_q(*selection_nonces)


def make_ciphertext_ballot_contest(
    object_id: str,
    description_hash: ElementModQ,
    ballot_selections: List[CiphertextBallotSelection],
    elgamal_public_key: ElementModP,
    crypto_extended_base_hash: ElementModQ,
    proof_seed: ElementModQ,
    number_elected: int,
    crypto_hash: Optional[ElementModQ] = None,
    proof: Optional[ConstantChaumPedersenProof] = None,
    nonce: Optional[ElementModQ] = None,
) -> CiphertextBallotContest:
    """
    Constructs a `CipherTextBallotContest` object. Most of the parameters here match up to fields
    in the class, but this helper function will optionally compute a Chaum-Pedersen proof if the
    ballot selections include their encryption nonces. Likewise, if a crypto_hash is not provided,
    it will be derived from the other fields.
    """
    if crypto_hash is None:
        crypto_hash = _ciphertext_ballot_context_crypto_hash(
            object_id, ballot_selections, description_hash
        )

    aggregate = _ciphertext_ballot_contest_aggregate_nonce(object_id, ballot_selections)
    if proof is None:
        proof = flatmap_optional(
            aggregate,
            lambda ag: make_constant_chaum_pedersen(
                message=_ciphertext_ballot_elgamal_accumulate(ballot_selections),
                constant=number_elected,
                r=ag,
                k=elgamal_public_key,
                seed=proof_seed,
                hash_header=crypto_extended_base_hash,
            ),
        )
    return CiphertextBallotContest(
        object_id=object_id,
        description_hash=description_hash,
        ballot_selections=ballot_selections,
        nonce=nonce,
        crypto_hash=crypto_hash,
        proof=proof,
    )


@dataclass(unsafe_hash=True)
class PlaintextBallot(ElectionObjectBase):
    """
    A PlaintextBallot represents a voters selections for a given ballot and ballot style
    :field object_id: A unique Ballot ID that is relevant to the external system
    """

    ballot_style: str
    """The `object_id` of the `BallotStyle` in the `Election` Manifest"""

    contests: List[PlaintextBallotContest]
    """The list of contests for this ballot"""

    def is_valid(self, expected_ballot_style_id: str) -> bool:
        """
        Check if expected ballot style is valid
        :param expected_ballot_style_id: Expected ballot style id
        :return: True if valid
        """
        if self.ballot_style != expected_ballot_style_id:
            log_warning(
                f"invalid ballot_style: for: {self.object_id} expected({expected_ballot_style_id}) actual({self.ballot_style})"
            )
            return False

        return True

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, PlaintextBallot)
            and self.ballot_style == other.ballot_style
            and _list_eq(self.contests, other.contests)
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


@dataclass(unsafe_hash=True)
class CiphertextBallot(ElectionObjectBase, CryptoHashCheckable):
    """
    A CiphertextBallot represents a voters encrypted selections for a given ballot and ballot style.

    When a ballot is in it's complete, encrypted state, the `nonce` is the master nonce
    from which all other nonces can be derived to encrypt the ballot.  Allong with the `nonce`
    fields on `Ballotcontest` and `BallotSelection`, this value is sensitive.

    Don't make this directly. Use `make_ciphertext_ballot` instead.
    :field object_id: A unique Ballot ID that is relevant to the external system
    """

    ballot_style: str
    """The `object_id` of the `BallotStyle` in the `Election` Manifest"""

    description_hash: ElementModQ
    """Hash of the election metadata"""

    previous_tracking_hash: ElementModQ
    """Previous tracking hash or seed hash"""

    contests: List[CiphertextBallotContest]
    """List of contests for this ballot"""

    tracking_hash: Optional[ElementModQ]
    """Unique ballot tracking hash for this ballot"""

    timestamp: int
    """Timestamp at which the ballot encryption is generated in tick"""

    crypto_hash: ElementModQ
    """The hash of the encrypted ballot representation"""

    nonce: Optional[ElementModQ]
    """The nonce used to encrypt this ballot. Sensitive & should be treated as a secret"""

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, CiphertextBallot)
            and self.object_id == other.object_id
            and self.ballot_style == other.ballot_style
            and self.description_hash == other.description_hash
            and self.previous_tracking_hash == other.previous_tracking_hash
            and _list_eq(self.contests, other.contests)
            and self.tracking_hash == other.tracking_hash
            and self.timestamp == other.timestamp
            and self.crypto_hash == other.crypto_hash
            and self.nonce == other.nonce
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    @staticmethod
    def nonce_seed(
        description_hash: ElementModQ, object_id: str, nonce: ElementModQ
    ) -> ElementModQ:
        """
        :return: a representation of the election and the external Id in the nonce's used
        to derive other nonce values on the ballot
        """
        return hash_elems(description_hash, object_id, nonce)

    def hashed_ballot_nonce(self) -> Optional[ElementModQ]:
        """
        :return: a hash value derived from the description hash, the object id, and the nonce value
                suitable for deriving other nonce values on the ballot
        """

        if self.nonce is None:
            log_warning(
                f"missing nonce for ballot {self.object_id} could not derive from null nonce"
            )
            return None

        return self.nonce_seed(self.description_hash, self.object_id, self.nonce)

    def get_tracker_code(self) -> Optional[str]:
        """
        Get a tracker hash as a code in friendly readable words for sharing
        :return: Tracker in words or None
        """
        if not self.tracking_hash:
            return None
        return tracker_hash_to_words(self.tracking_hash)

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted Ballot, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `description_hash` and `ballot_selections`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.
        """
        if len(self.contests) == 0:
            log_warning(
                f"mismatching contests state: {self.object_id} expected(some), actual(none)"
            )
            return ZERO_MOD_Q

        contest_hashes = [contest.crypto_hash for contest in self.contests]
        return hash_elems(self.object_id, seed_hash, *contest_hashes)

    def is_valid_encryption(
        self,
        seed_hash: ElementModQ,
        elgamal_public_key: ElementModP,
        crypto_extended_base_hash: ElementModQ,
    ) -> bool:
        """
        Given an encrypted Ballot, validates the encryption state against a specific seed hash and public key
        by verifying the states of this ballot's children (BallotContest's and BallotSelection's).
        Calling this function expects that the object is in a well-formed encrypted state
        with the `contests` populated with valid encrypted ballot selections,
        and the ElementModQ `description_hash` also populated.
        Specifically, the seed hash in this context is the hash of the Election Manifest, 
        or whatever `ElementModQ` was used to populate the `description_hash` field.
        """

        if seed_hash != self.description_hash:
            log_warning(
                f"mismatching ballot hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.description_hash)})"
            )
            return False

        recalculated_crypto_hash = self.crypto_hash_with(seed_hash)
        if self.crypto_hash != recalculated_crypto_hash:
            log_warning(
                f"mismatching crypto hash: {self.object_id} expected({str(recalculated_crypto_hash)}), actual({str(self.crypto_hash)})"
            )
            return False

        # Check the proofs on the ballot
        valid_proofs: List[bool] = list()

        for contest in self.contests:
            for selection in contest.ballot_selections:
                valid_proofs.append(
                    selection.is_valid_encryption(
                        selection.description_hash,
                        elgamal_public_key,
                        crypto_extended_base_hash,
                    )
                )
            valid_proofs.append(
                contest.is_valid_encryption(
                    contest.description_hash,
                    elgamal_public_key,
                    crypto_extended_base_hash,
                )
            )
        return all(valid_proofs)


class BallotBoxState(Enum):
    """
    Enumeration used when marking a ballot as cast or spoiled
    """

    CAST = 1
    """
    A ballot that has been explicitly cast
    """
    SPOILED = 2
    """
    A ballot that has been explicitly spoiled
    """
    UNKNOWN = 999
    """
    A ballot whose state is unknown to ElectionGuard and will not be included in any election results
    """


@dataclass(unsafe_hash=True)
class CiphertextAcceptedBallot(CiphertextBallot):
    """
    A `CiphertextAcceptedBallot` represents a ballot that is accepted for inclusion in election results.
    An accepted ballot is or is about to be either cast or spoiled.
    The state supports the `BallotBoxState.UNKNOWN` enumeration to indicate that this object is mutable
    and has not yet been explicitly assigned a specific state.

    Note, additionally, this ballot includes all proofs but no nonces.

    Do not make this class directly. Use `make_ciphertext_accepted_ballot` or `from_ciphertext_ballot` instead.
    """

    state: BallotBoxState

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, CiphertextAcceptedBallot)
            and super.__eq__(self, other)
            and self.state == other.state
        )

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)


def make_ciphertext_ballot(
    object_id: str,
    ballot_style: str,
    description_hash: ElementModQ,
    previous_tracking_hash: Optional[ElementModQ],
    contests: List[CiphertextBallotContest],
    nonce: Optional[ElementModQ] = None,
    timestamp: Optional[int] = None,
    tracking_hash: Optional[ElementModQ] = None,
) -> CiphertextBallot:
    """
    Makes a `CiphertextBallot`, initially in the state where it's neither been cast nor spoiled.

    :param object_id: the object_id of this specific ballot
    :param ballot_style: The `object_id` of the `BallotStyle` in the `Election` Manifest
    :param description_hash: Hash of the election metadata
    :param crypto_base_hash: Hash of the cryptographic election context
    :param contests: List of contests for this ballot
    :param timestamp: Timestamp at which the ballot encryption is generated in tick
    :param previous_tracking_hash: Previous tracking hash or seed hash
    :param nonce: optional nonce used as part of the encryption process
    """

    if len(contests) == 0:
        log_warning(f"ciphertext ballot with no contests")

    contest_hashes = [contest.crypto_hash for contest in contests]
    contest_hash = hash_elems(object_id, description_hash, *contest_hashes)

    timestamp = to_ticks(datetime.utcnow()) if timestamp is None else timestamp
    if previous_tracking_hash is None:
        previous_tracking_hash = description_hash
    if tracking_hash is None:
        tracking_hash = get_rotating_tracker_hash(
            previous_tracking_hash, timestamp, contest_hash
        )

    return CiphertextBallot(
        object_id=object_id,
        ballot_style=ballot_style,
        description_hash=description_hash,
        previous_tracking_hash=previous_tracking_hash,
        contests=contests,
        tracking_hash=tracking_hash,
        timestamp=timestamp,
        nonce=nonce,
        crypto_hash=contest_hash,
    )


def make_ciphertext_accepted_ballot(
    object_id: str,
    ballot_style: str,
    description_hash: ElementModQ,
    previous_tracking_hash: Optional[ElementModQ],
    contests: List[CiphertextBallotContest],
    tracking_hash: Optional[ElementModQ],
    timestamp: Optional[int] = None,
    state: BallotBoxState = BallotBoxState.UNKNOWN,
) -> CiphertextAcceptedBallot:
    """
    Makes a `CiphertextAcceptedBallot`, ensuring that no nonces are part of the contests.

    :param object_id: the object_id of this specific ballot
    :param ballot_style: The `object_id` of the `BallotStyle` in the `Election` Manifest
    :param description_hash: Hash of the election metadata
    :param previous_tracking_hash: Previous tracking hash or seed hash
    :param contests: List of contests for this ballot
    :param timestamp: Timestamp at which the ballot encryption is generated in tick
    :param state: ballot box state
    """

    if len(contests) == 0:
        log_warning(f"ciphertext ballot with no contests")

    contest_hashes = [contest.crypto_hash for contest in contests]
    contest_hash = hash_elems(object_id, description_hash, *contest_hashes)

    timestamp = to_ticks(datetime.utcnow()) if timestamp is None else timestamp
    if previous_tracking_hash is None:
        previous_tracking_hash = description_hash
    if tracking_hash is None:
        tracking_hash = get_rotating_tracker_hash(
            previous_tracking_hash, timestamp, contest_hash
        )

    # copy the contests and selections, removing all nonces
    new_contests: List[CiphertextBallotContest] = []
    for contest in contests:
        new_selections = [
            replace(selection, nonce=None) for selection in contest.ballot_selections
        ]
        new_contest = replace(contest, nonce=None, ballot_selections=new_selections)
        new_contests.append(new_contest)

    return CiphertextAcceptedBallot(
        object_id=object_id,
        ballot_style=ballot_style,
        description_hash=description_hash,
        previous_tracking_hash=previous_tracking_hash,
        contests=new_contests,
        tracking_hash=tracking_hash,
        timestamp=timestamp,
        crypto_hash=contest_hash,
        nonce=None,
        state=state,
    )


def from_ciphertext_ballot(
    ballot: CiphertextBallot, state: BallotBoxState = BallotBoxState.UNKNOWN
) -> CiphertextAcceptedBallot:
    """
    Convert a `CiphertextBallot` into a `CiphertextAcceptedBallot`, with all nonces removed.
    """
    return make_ciphertext_accepted_ballot(
        object_id=ballot.object_id,
        ballot_style=ballot.ballot_style,
        description_hash=ballot.description_hash,
        contests=ballot.contests,
        timestamp=ballot.timestamp,
        previous_tracking_hash=ballot.previous_tracking_hash,
        tracking_hash=ballot.tracking_hash,
        state=state,
    )
