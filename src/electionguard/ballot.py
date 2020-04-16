from dataclasses import dataclass, field
from typing import Optional, List

from .serializable import Serializable
from .group import ElementModP, ElementModQ, ZERO_MOD_Q
from .hash import CryptoHashCheckable, hashable_element, flatten, hash_elems
from .is_valid import IsValid, IsValidEncryption
from .chaum_pedersen import ConstantChaumPedersenProof, DisjunctiveChaumPedersenProof
from .elgamal import ElGamalCiphertext, elgamal_add

from .election import Contest, Selection
from .logs import log_warning

@dataclass
class BallotSelection(Selection, IsValid, IsValidEncryption, CryptoHashCheckable):
    """
    A BallotSelection represents an individual selection on a ballt.

    This class accepts a `plaintext` string field which has no constraints 
    in the ElectionGuard Data Specitification, but is constrained logically 
    in the application to resolve to `True` or `False`.  This implies the Data
    Specification supports passing cleartext values for writeins, but these values
    are discarded by the current implementation when encrypting.

    When a selection is encrypted, the state should be mutated such that the
    `plaintext` value is destroyed and the `message`, `crypto_hash`, `nonce`, and
    `proof` fields are populated.

    A consumer of this object has the option to discard the `nonce` or discard the `proof`,
    or keep both values.  By discarding the `nonce`, the encrypted representation and proofs
    cannot be regenerated.  By keeping the `nonce`, an external system can regenerate the proofs
    on demand.  This is useful for storage or memory constrained systems. 
    """

    # determines if this is a placeholder selection
    is_placeholder_selection: Optional[bool] = field(default=None)

    # the plaintext representation of the selection (usually `True` or `False`)
    plaintext: Optional[str] = field(default=None)

    # The encrypted representation of the plaintext field
    message: Optional[ElGamalCiphertext] = field(default=None)

    # The SelectionDescription hash 
    # TODO: determine if caching this value is necessary given it can be regenerated
    selection_hash: Optional[ElementModQ] = field(default=None)

    # The hash of the encrypted values
    crypto_hash: Optional[ElementModQ] = field(default=None)

    # The nonce used to generate the encryption
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    # the proof that demonstrates the selection is an encryption of 0 or 1,
    # and was encrypted using the `nonce`
    proof: Optional[DisjunctiveChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:
        """
        Given a BallotSelection returns true if the data conforms to 
        `is_plaintext_state` or `is_encrypted_state`
        """

        return self.is_plaintext_state() or self.is_encrypted_state()

    def is_plaintext_state(self) -> bool:
        """
        Given a BallotSelection returns true if the state is encrypted
        """
        return self.plaintext is not None \
            and self.message is None \
            and self.crypto_hash is None \
            and self.proof is None

    def is_encrypted_state(self) -> bool:
        """
        Given a BallotSelection returns the data state when the selection is encrypted
        """
        return self.is_placeholder_selection is not None \
            and self.plaintext is None \
            and self.message is not None \
            and self.crypto_hash is not None \
            and self.selection_hash is not None \
            and self.proof is not None

    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
        """
        Given an encrypted BallotSelection, validates the encryption state against a specific seed hash and public key.
        Calling this function expects that the object is in a well-formed encrypted state
        with the elgamal encrypted `message` field populated along with the DisjunctiveChaumPedersenProof `proof`,
        the ElementModQ `selection_hash` and the ElementModQ `crypto_hash`. 
        Specifically, the seed hash in this context is the hash of the SelectionDescription, 
        or whatever `ElementModQ` was used to populate the `selection_hash` field.
        """
        if self.is_plaintext_state():
            log_warning(
                f"mismatching selection state: {self.object_id} expected(encrypted), actual(plaintext)"
            )
            return False

        if not self.is_encrypted_state():
            log_warning(
                f"mismatching selection state: {self.object_id} expected(encrypted), actual(invalid)"
            )
            return False

        if seed_hash != self.selection_hash:
            log_warning(
                f"mismatching selection hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.selection_hash)})"
            )
            return False

        recalculated_crypto_hash = self.crypto_hash_with(seed_hash)
        if self.crypto_hash is not recalculated_crypto_hash:
            log_warning(
                f"mismatching crypto hash: {self.object_id} expected({str(recalculated_crypto_hash)}), actual({str(self.crypto_hash)})"
            )
            return False

        return self.proof.is_valid(self.message, elgamal_public_key)

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted BallotSelection, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `selection_hash` and `message`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.
        """
        if self.selection_hash is None:
            self.selection_hash = seed_hash

        if self.message is None:
            log_warning(
                f"mismatching message state: {self.object_id} expected(encrypted), actual(invalid)"
            )
            return ZERO_MOD_Q

        self.crypto_hash = hash_elems(self.selection_hash, self.message.crypto_hash())
        return self.crypto_hash

@dataclass
class BallotContest(Contest, IsValid, CryptoHashCheckable):
    """
    A BallotContest represents the selections made by a voter for a specific ContestDescription

    This class is stateful with respect to it's child values (BallotSelections) and can be in
    `plaintext` or `encrypted` state.

    BallotContest can also be a partial or a complete representation of a contest dataset.  Specifically,
    a partial representation must include at a minimum the "affirmative" selections of a contest.
    A complete representation of a ballot must include both affirmative and negative selections of
    the contest, AND the placeholder selections necessary to satisfy the ConstantChaumPedersen proof.

    Typically partial contests are passed into Electionguard, while complete contests are passed
    from ElectionGuard.
    """

    # collection of ballot selections
    ballot_selections: List[BallotSelection] = field(default_factory=lambda: [])

    # Hash from contestDescription
    contest_hash: Optional[ElementModQ] = field(default=None)

    # Hash of the encrypted values
    crypto_hash: Optional[ElementModQ] = field(default=None)

    # the nonce used to generate the encryption
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    # the proof demonstrates the sum of the selections does not exceed the maximum
    # available selections for the contest, and that the proof was generated with the nonce
    proof: Optional[ConstantChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:
        """
        Given a BallotContest returns true if the data conforms to 
        `is_plaintext_state` or `is_encrypted_state`
        """
        selections_valid: List[bool] = list()
        for selection in self.ballot_selections:
            selections_valid.append(selection.is_valid())

        # TODO: verify hash if not None
        # TODO: verify proof if not None
        return self.is_plaintext_state() or self.is_encrypted_state()

    def is_plaintext_state(self) -> bool:
        """
        Given a BallotContest returns true if the state is plaintext
        """
        children_valid: List[bool] = list()
        for selection in self.ballot_selections:
            children_valid.append(selection.is_plaintext_state())

        return all(children_valid) and self.crypto_hash is None and self.proof is None

    def is_encrypted_state(self) -> bool:
        """
        Given a BallotContest returns true if the state is encrypted
        """
        children_valid: List[bool] = list()
        for selection in self.ballot_selections:
            children_valid.append(selection.is_encrypted_state())
        
        return all(children_valid) and self.crypto_hash is not None and self.proof is not None

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted BallotContest, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `contest_hash` and `ballot_selections`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.
        """
        if self.contest_hash is None:
            self.contest_hash = seed_hash

        if len(self.ballot_selections) == 0:
            log_warning(
                f"mismatching ballot_selections state: {self.object_id} expected(some), actual(none)"
            )
            return ZERO_MOD_Q

        selection_hashes = [selection.crypto_hash for selection in self.ballot_selections]

        self.crypto_hash = hash_elems(self.contest_hash, *selection_hashes)
        return self.crypto_hash

    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
        """
        Given an encrypted BallotContest, validates the encryption state against a specific seed hash and public key
        by verifying the accumulated sum of selections match the proof.
        Calling this function expects that the object is in a well-formed encrypted state
        with the `ballot_selections` populated with valid encrypted ballot selections,
        the ElementModQ `contest_hash`, the ElementModQ `crypto_hash`, and the ConstantChaumPedersenProof all populated. 
        Specifically, the seed hash in this context is the hash of the ContestDescription, 
        or whatever `ElementModQ` was used to populate the `contest_hash` field.
        """
        if self.is_plaintext_state():
            log_warning(
                f"mismatching contest state: {self.object_id} expected(encrypted), actual(plaintext)"
            )
            return False

        if not self.is_encrypted_state():
            log_warning(
                f"mismatching contest state: {self.object_id} expected(encrypted), actual(invalid)"
            )
            return False

        if seed_hash != self.contest_hash:
            log_warning(
                f"mismatching contest hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.contest_hash)})"
            )
            return False

        # NOTE: this check does not verify the proof of the individual selections.

        # Verify the sum of the selections matches the proof
        elgamal_accumulation = elgamal_add(*[selection.message for selection in self.ballot_selections])
        return self.proof.is_valid(elgamal_accumulation, elgamal_public_key)

@dataclass
class Ballot(Serializable, IsValid, CryptoHashCheckable):
    """
    A Ballot represents a voters selections for a given ballot and ballot style

    This class is stateful with respect to it's child values (BallotContest's) and can be in
    `plaintext` or `encrypted` state.

    When a ballot is in it's complete, encrypted state, the `nonce` is the master nonce
    from which all other nonces can be derived to encrypt the ballot.  Allong with the `nonce`
    fields on `Ballotcontest` and `BallotSelection`, this value is sensitive
    
    """

    # A unique Ballot ID that is relevant to the external system
    object_id: str

    # The `object_id` of the `BallotStyl` in the `Election` Manifest
    ballot_style: str

    # The list of contests for this ballot
    contests: List[BallotContest]

    # The hash of the election metadata
    ballot_hash: Optional[ElementModQ] = field(default=None)

    # the hash of the encrypted ballot representation
    crypto_hash: Optional[ElementModQ] = field(default=None)

    # the unique ballot tracking id for this ballot
    tracking_id: Optional[str] = field(default=None)

    # the nonce used to encrypt this ballot
    # this value is sensitive & should be treated as a secret
    nonce: Optional[ElementModQ] = field(default=None)

    def is_plaintext_state(self) -> bool:

        children_valid: List[bool] = list()
        for contest in self.contests:
            children_valid.append(contest.is_plaintext_state())

        return self.tracking_id is None \
            and self.nonce is None \
            and all(children_valid)

    def is_encrypted_state(self) -> bool:
        children_valid: List[bool] = list()
        for contest in self.contests:
            children_valid.append(contest.is_encrypted_state())

        return self.tracking_id is not None \
            and self.crypto_hash is not None \
            and all(children_valid)

    def is_valid(self) -> bool:
        """
        """

        # TODO: verify hash if not None
        return self.is_plaintext_state() or self.is_encrypted_state()

    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Given an encrypted Ballot, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash examines
        the `contest_hash` and `ballot_selections`, but not the proof.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Disjunctive Chaum-Pedersen proofs might be computed
        later on.
        """
        if self.ballot_hash is None:
            self.ballot_hash = seed_hash

        if len(self.contests) == 0:
            log_warning(
                f"mismatching contests state: {self.object_id} expected(some), actual(none)"
            )
            return ZERO_MOD_Q

        contest_hashes = [contest.crypto_hash for contest in self.contests]

        self.crypto_hash = hash_elems(self.ballot_hash, *contest_hashes)
        return self.crypto_hash
        
    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
        """
        Given an encrypted Ballot, validates the encryption state against a specific seed hash and public key
        by verifying the states of this ballot's children (BallotContest's and BallotSelection's).
        Calling this function expects that the object is in a well-formed encrypted state
        with the `contests` populated with valid encrypted ballot selections,
        and the ElementModQ `ballot_hash` also populated.
        Specifically, the seed hash in this context is the hash of the Election Manifest, 
        or whatever `ElementModQ` was used to populate the `ballot_hash` field.
        """

        if seed_hash != self.ballot_hash:
            log_warning(
                f"mismatching ballot hash: {self.object_id} expected({str(seed_hash)}), actual({str(self.ballot_hash)})"
            )
            return False

        valid_proofs: List[bool] = list()

        for contest in self.contests:
            for selection in contest.ballot_selections:
                valid_proofs.append(
                    selection.is_valid_encryption(
                        selection.selection_hash, 
                        elgamal_public_key
                    )
                )
            valid_proofs.append(
                contest.is_valid_encryption(
                    contest.contest_hash, 
                    elgamal_public_key
                )
            )
        return all(valid_proofs)

