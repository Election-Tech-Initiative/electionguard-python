from dataclasses import dataclass, field
from distutils import util
from typing import Optional, List

from .serializable import Serializable
from .group import add_q, ElementModP, ElementModQ, ZERO_MOD_Q
from .hash import CryptoHashCheckable, hash_elems
from .is_valid import IsValid, IsValidEncryption
from .chaum_pedersen import ConstantChaumPedersenProof, DisjunctiveChaumPedersenProof
from .elgamal import ElGamalCiphertext, elgamal_add

from .election import Contest, Selection
from .logs import log_warning

@dataclass
class PlaintextBallotSelection(Selection, IsValid):
    """
    A BallotSelection represents an individual selection on a ballot.

    This class accepts a `plaintext` string field which has no constraints 
    in the ElectionGuard Data Specitification, but is constrained logically 
    in the application to resolve to `True` or `False`.  This implies that the
    data specification supports passing any string that can be represented as
    an integer, however only 0 and 1 is supported for now.

    This class can also be designated as `is_placeholder_selection` which has no
    context to the data specification but is useful for running validity checks internally

    an `extra_data` field exists to support any arbitrary data to be associated
    with the selection.  In practice, this field is the cleartext representation
    of a write-in candidate value.  In the current implementation these values are
    discarded when encrypting.
    """

    # the plaintext representation of the selection (usually `True` or `False`)
    plaintext: str

    # determines if this is a placeholder selection
    is_placeholder_selection: bool = field(default=False)

    # an optional field of arbitrary data
    extra_data: Optional[str] = field(default=None)

    def is_valid(self, expected_object_id: str) -> bool:
        """
        Given a PlaintextBallotSelection validates that the object matches an expected object
        and that the plaintext string can resolve to a valid representation
        """

        if self.object_id != expected_object_id:
            log_warning(f"invalid object_id: expected({expected_object_id}) actual({self.object_id})")
            return False

        choice = self.to_int()
        if choice < 0 or choice > 1:
            log_warning(f"Currently only supporting choices of 0 or 1: {str(self)}")
            return False

        return True

    def to_int(self) -> int:
        """
        represent a Truthy string as 1, or if the string is Falsy, 0
        See: https://docs.python.org/3/distutils/apiref.html#distutils.util.strtobool

        :param from_string: a string representing "true" or "false"
        :return: an integer 0 or 1 for valid data, or 0 if the data is malformed
        """

        # TODO: Support integer votes greater than 1 for cases such as cumulative voting

        as_bool = False
        try:
            as_bool = util.strtobool(self.plaintext.lower())
        except ValueError:
            log_warning(f"to_int could not convert plaintext: {self.plaintext.lower()} to bool")

        as_int = int(as_bool)
        return as_int

@dataclass
class CyphertextBallotSelection(Contest, IsValidEncryption, CryptoHashCheckable):
    """
    A CyphertextBallotSelection represents an individual encrypted selection on a ballot.

    This class accepts a `description_hash` and a `message` as required parameters
    in its constructor.

    When a selection is encrypted, the `description_hash` and `message` required fields must
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
    
    # The SelectionDescription hash 
    description_hash: ElementModQ

    # The encrypted representation of the plaintext field
    message: ElGamalCiphertext

    # determines if this is a placeholder selection
    is_placeholder_selection: bool = field(default=False)

    # The nonce used to generate the encryption
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    # The hash of the encrypted values
    crypto_hash: ElementModQ = field(init=False)

    # the proof that demonstrates the selection is an encryption of 0 or 1,
    # and was encrypted using the `nonce`
    proof: Optional[DisjunctiveChaumPedersenProof] = field(default=None)

    def __post_init__(self):
        self.crypto_hash = self.crypto_hash_with(self.description_hash)

    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
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

        return self.proof.is_valid(self.message, elgamal_public_key)

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

        return hash_elems(seed_hash, self.message.crypto_hash())

@dataclass
class PlaintextBallotContest(Contest, IsValid):
    """
    A PlaintextBallotContest represents the selections made by a voter for a specific ContestDescription

    this class can be either a partial or a complete representation of a contest dataset.  Specifically,
    a partial representation must include at a minimum the "affirmative" selections of a contest.
    A complete representation of a ballot must include both affirmative and negative selections of
    the contest, AND the placeholder selections necessary to satisfy the ConstantChaumPedersen proof 
    in the CyphertextBallotContest.

    Typically partial contests are passed into Electionguard for memory constrained systems, 
    while complete contests are passed into ElectionGuard when running encryption on an existing dataset.
    """

    # collection of ballot selections
    ballot_selections: List[PlaintextBallotSelection] = field(default_factory=lambda: [])

    def is_valid(
        self, expected_object_id: str, expected_number_slections: int, expected_number_elected: int, votes_allowed: int) -> bool:
        """
        Given a PlaintextBallotContest returns true if the state is representative of the expected values.

        Note: because this class supports partial representations, undervotes are considered a valid state.
        """

        if self.object_id != expected_object_id:
            log_warning(f"invalid object_id: expected({expected_object_id}) actual({self.object_id})")
            return False

        if len(self.ballot_selections) > expected_number_slections:
            log_warning(f"invalid number_slections: expected({expected_number_slections}) actual({len(self.ballot_selections)})")
            return False

        number_elected = 0
        votes = 0

        # Verify the selections are well-formed
        children_valid: List[bool] = list()
        for selection in self.ballot_selections: 
            selection_count = selection.to_int()
            votes += selection_count
            if selection_count >= 1:
                number_elected += 1

        if number_elected > expected_number_elected:
            log_warning(f"invalid number_elected: expected({expected_number_elected}) actual({number_elected})")
            return False
        
        if votes > votes_allowed:
            log_warning(f"invalid votes: expected({votes_allowed}) actual({votes})")
            return False

        return True

@dataclass
class CyphertextBallotContest(Contest, IsValidEncryption, CryptoHashCheckable):
    """
    A CyphertextBallotContest represents the selections made by a voter for a specific ContestDescription

    CyphertextBallotContest can only be a complete representation of a contest dataset.  While
    PlaintextBallotContest supports a partial representation, a CyphertextBallotContest includes all data
    necessary for a verifier to verify the contest.  Specifically, it includes both explicit affirmative 
    and negative selections of the contest, as well as the placeholder selections that satisfy
    the ConstantChaumPedersen proof.

    Similar to `CyphertextBallotSelection` the consuming application can choose to discard or keep both
    the `nonce` and the `proof` in some circumstances.  For deterministic nonce's derived from the 
    master nonce, both values can be regenerated.  If the `nonce` for this contest is completely random,
    then it is required in order to regenerate the proof.
    """

    # Hash from contestDescription
    description_hash: ElementModQ

    # collection of ballot selections
    ballot_selections: List[CyphertextBallotSelection]

    # Hash of the encrypted values
    crypto_hash: ElementModQ = field(init=False)

    # the nonce used to generate the encryption
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    # the proof demonstrates the sum of the selections does not exceed the maximum
    # available selections for the contest, and that the proof was generated with the nonce
    proof: Optional[ConstantChaumPedersenProof] = field(default=None)

    def __post_init__(self):
        self.crypto_hash = self.crypto_hash_with(self.description_hash)

    def aggregate_nonce(self) -> ElementModQ:
        """
        :return: an aggregate nonce for the contest composed of the nonces of the selections
        """
        return add_q(*[selection.nonce for selection in self.ballot_selections])

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

        if len(self.ballot_selections) == 0:
            log_warning(
                f"mismatching ballot_selections state: {self.object_id} expected(some), actual(none)"
            )
            return ZERO_MOD_Q

        selection_hashes = [selection.crypto_hash for selection in self.ballot_selections]

        return hash_elems(seed_hash, *selection_hashes)

    def elgamal_accumulate(self) -> ElGamalCiphertext:
        """
        add the individual ballot_selections `message` fields together
        """
        return elgamal_add(*[selection.message for selection in self.ballot_selections])

    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
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

        # Verify the sum of the selections matches the proof
        elgamal_accumulation = self.elgamal_accumulate()
        return self.proof.is_valid(elgamal_accumulation, elgamal_public_key)

@dataclass
class PlaintextBallot(Serializable, IsValid):
    """
    A PlaintextBallot represents a voters selections for a given ballot and ballot style
    """

    # A unique Ballot ID that is relevant to the external system
    object_id: str

    # The `object_id` of the `BallotStyl` in the `Election` Manifest
    ballot_style: str

    # The list of contests for this ballot
    contests: List[PlaintextBallotContest]

    def is_valid(self, expected_ballot_style_id: str) -> bool:

        if self.ballot_style != expected_ballot_style_id:
            log_warning(f"invalid ballot_style: for: {self.object_id} expected({expected_ballot_style_id}) actual({self.ballot_style})")
            return False

        # TODO: Check count of contests?

        return True

@dataclass
class CyphertextBallot(Serializable, IsValid, CryptoHashCheckable):
    """
    A CyphertextBallot represents a voters encrypted selections for a given ballot and ballot style

    When a ballot is in it's complete, encrypted state, the `nonce` is the master nonce
    from which all other nonces can be derived to encrypt the ballot.  Allong with the `nonce`
    fields on `Ballotcontest` and `BallotSelection`, this value is sensitive.
    """

    # A unique Ballot ID that is relevant to the external system
    object_id: str

    # The `object_id` of the `BallotStyl` in the `Election` Manifest
    ballot_style: str

    # The hash of the election metadata
    description_hash: ElementModQ

    # The list of contests for this ballot
    contests: List[CyphertextBallotContest]

    # the hash of the encrypted ballot representation
    crypto_hash: ElementModQ = field(init=False)

    # the nonce used to encrypt this ballot
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    # the unique ballot tracking id for this ballot
    tracking_id: Optional[str] = field(default=None)

    def __post_init__(self):
        self.crypto_hash = self.crypto_hash_with(self.description_hash)

    def is_valid(self) -> bool:
        """
        """
        children_valid: List[bool] = list()
        for contest in self.contests:
            children_valid.append(contest.is_valid())

        return self.tracking_id is not None \
            and all(children_valid)

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
        return hash_elems(seed_hash, *contest_hashes)
        
    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
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
                        elgamal_public_key
                    )
                )
            valid_proofs.append(
                contest.is_valid_encryption(
                    contest.description_hash, 
                    elgamal_public_key
                )
            )
        return all(valid_proofs)

