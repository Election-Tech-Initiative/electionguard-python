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
    is_placeholder_selection: Optional[bool] = field(default=None)
    plaintext: Optional[str] = field(default=None)
    message: Optional[ElGamalCiphertext] = field(default=None)
    # The SelectionDescription hash not convinced we need to cache this given it can be regenerated
    selection_hash: Optional[ElementModQ] = field(default=None)
    # 
    crypto_hash: Optional[ElementModQ] = field(default=None)
    nonce: Optional[ElementModQ] = field(default=None)
    proof: Optional[DisjunctiveChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:
        """
        Given a BallotSelection returns true if the data conforms to `is_plaintext_state` or `is_encrypted_state`
        """

        return self.is_plaintext_state() or self.is_encrypted_state()

    def is_plaintext_state(self) -> bool:
        """
        Given a BallotSelection returns true if the state is plaintext
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
    ballot_selections: List[BallotSelection] = field(default_factory=lambda: [])
    # Hash from contestDescription
    contest_hash: Optional[ElementModQ] = field(default=None)
    crypto_hash: Optional[ElementModQ] = field(default=None)
    nonce: Optional[ElementModQ] = field(default=None)
    proof: Optional[ConstantChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:

        selections_valid: List[bool] = list()
        for selection in self.ballot_selections:
            selections_valid.append(selection.is_valid())

        # TODO: verify hash if not None
        # TODO: verify proof if not None
        return all(selections_valid)

    def is_plaintext_state(self) -> bool:

        selections_plaintext: List[bool] = list()
        for selection in self.ballot_selections:
            selections_plaintext.append(selection.is_plaintext_state())

        return all(selections_plaintext) and self.crypto_hash is None and self.proof is None

    def is_encrypted_state(self) -> bool:

        selections_encrypted: List[bool] = list()
        for selection in self.ballot_selections:
            selections_encrypted.append(selection.is_encrypted_state())
        
        return all(selections_encrypted) and self.crypto_hash is not None and self.proof is not None

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
        or whatever `ElementModQ` was used to populate the `selection_hash` field.
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
    """
    object_id: str
    ballot_style: str
    contests: List[BallotContest]
    ballot_hash: Optional[ElementModQ] = field(default=None)
    crypto_hash: Optional[ElementModQ] = field(default=None)
    tracking_id: Optional[str] = field(default=None)

    nonce: Optional[ElementModQ] = field(default=None)

    def is_valid(self) -> bool:
        """
        """
        contests_valid: List[bool] = list()
        for contest in self.contests:
            contests_valid.append(contest.is_valid())

        is_valid_in_state = self.tracking_id is None \
            and self.crypto_hash is None

        is_valid_out_state = self.tracking_id is not None \
            and self.crypto_hash is not None

        # TODO: verify hash if not None
        return (is_valid_in_state or is_valid_out_state) and all(contests_valid)

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

