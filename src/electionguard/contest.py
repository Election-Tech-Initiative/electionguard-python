from typing import NamedTuple, List, Optional
from functools import reduce

from electionguard.chaum_pedersen import (
    DisjunctiveChaumPedersenProof,
    ConstantChaumPedersenProof,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
)
from electionguard.elgamal import (
    ElGamalCiphertext,
    elgamal_encrypt,
    elgamal_add,
    ElGamalKeyPair,
)
from electionguard.group import ElementModQ, ElementModP, add_q, flatmap_optional
from electionguard.hash import hash_elems
from electionguard.logs import log_warning
from electionguard.nonces import Nonces


class Candidate(NamedTuple):
    # Related to: https://developers.google.com/elections-data/reference/candidate
    ballot_name: str
    is_incumbent: bool
    is_dummy: bool  # ElectionGuard dummy candidates
    is_writein: bool


class ContestDescription(NamedTuple):
    # Related to: https://developers.google.com/elections-data/reference/contest
    abbreviation: str
    ballot_selections: List[Candidate]
    ballot_title: str
    ballot_subtitle: str
    electoral_district_id: str
    name: str
    number_elected: int  # the N in n-of-m
    votes_allowed: int  # the M in n-of-m, equal to len(ballot_selections)

    def crypto_hash(self) -> ElementModQ:
        """
        Given a ContestDescription, deterministically derives a "hash" of that contest,
        suitable for use in ElectionGuard's "base hash" values, and for validating that
        either a plaintext or encrypted voted context and its corresponding contest
        description match up.
        """

        # We could just use str(cd), but we want this to be easily reproducible outside Python
        candidate_hashes = [
            f"({s.ballot_name}/{str(s.is_incumbent)}/{str(s.is_dummy)}/{str(s.is_writein)})"
            for s in self.ballot_selections
        ]

        return hash_elems(
            self.abbreviation,
            self.ballot_title,
            self.ballot_subtitle,
            self.electoral_district_id,
            self.name,
            str(self.number_elected),
            str(self.votes_allowed),
            *candidate_hashes,
        )


class PlaintextVotedContest(NamedTuple):
    contest_hash: ElementModQ  # derived from a ContestDescription
    choices: List[int]
    # For the choices, 0 = no vote, 1 = vote, 2+ = reserved for RCV and such later on
    # And the indices into this list are the same as the indices into the ballot_selections

    def is_valid(self, cd: ContestDescription) -> bool:
        """
        Given a PlaintextVotedContest and its corresponding ContestDescription, validates
        that the plaintext well-formed and suitable for encryption. Returns true if good,
        false if not. Also generates a log warning explaining what's wrong.
        """
        h = cd.crypto_hash()
        if h != self.contest_hash:
            log_warning(
                f"mismatching contest hash: plaintext({str(self)}), contest description({str(cd)})"
            )
            return False

        total = 0
        for choice in self.choices:
            if choice < 0 or choice > 1:
                log_warning(f"Currently only supporting choices of 0 or 1: {str(self)}")
                return False
            total += choice

        if total != cd.number_elected:
            log_warning(f"Sum of choices doesn't match number_elected: {str(self)}")
            return False

        if (
            len(self.choices) != len(cd.ballot_selections)
            or len(self.choices) != cd.votes_allowed
        ):
            log_warning(
                f"Number of choices in ContestDescription doesn't match PlaintextVotedContest: {str(self)}"
            )
            return False

        return True


class EncryptedVotedContest(NamedTuple):
    contest_hash: ElementModQ  # derived from a ContestDescription
    encrypted_selections: List[ElGamalCiphertext]
    zero_or_one_selection_proofs: List[DisjunctiveChaumPedersenProof]
    sum_of_counters_proof: ConstantChaumPedersenProof

    def crypto_hash(self) -> ElementModQ:
        """
        Given an EncryptedVotedContest, generates a hash, suitable for rolling up
        into a hash / tracking code for an entire ballot. Of note, this particular hash only examines
        the `contest_hash` and `encrypted_selections`, but not the Chaum-Pedersen proofs.
        This is deliberate, allowing for the possibility of ElectionGuard variants running on
        much more limited hardware, wherein the Chaum-Pedersen proofs might be computed
        later on.
        """

        # Python doesn't have a flatmap operator, so we're first concatenating together
        # all the ElGamal pairs into a single List[ElementModP], which we can then
        # just feed into the hash function.

        flattened_votes: List[ElementModP] = reduce(
            lambda l, e: l + [e.alpha, e.beta], self.encrypted_selections, []
        )
        return hash_elems(self.contest_hash, *flattened_votes)

    def is_valid(self, cd: ContestDescription, elgamal_public_key: ElementModP) -> bool:
        """
        Given an EncryptedVotedContest and the corresponding ContestDescription
        and ElGamal public key, validates all the proofs. Returns
        true if everything is good, false otherwise and logs a warning.
        """

        (
            contest_hash,
            encrypted_selections,
            zero_or_one_selection_proofs,
            sum_of_counters_proof,
        ) = self

        if cd.crypto_hash() != contest_hash:
            log_warning(f"mismatching contest hashes, evc({str(self)}), cd({str(cd)})")
            return False

        num_slots = len(cd.ballot_selections)
        if len(encrypted_selections) != num_slots:
            log_warning(
                f"expected {num_slots} encrypted ballots, got {len(encrypted_selections)}: {str(self)}"
            )
            return False

        if len(zero_or_one_selection_proofs) != num_slots:
            log_warning(
                f"expected {num_slots} disjunctive Chaum-Pedersen proofs, got {len(zero_or_one_selection_proofs)}: {str(self)}"
            )
            return False

        for i in range(0, num_slots):
            if not zero_or_one_selection_proofs[i].is_valid(
                encrypted_selections[i], elgamal_public_key
            ):
                # log warning already happened if this failed
                return False

        elgamal_accumulation = elgamal_add(*encrypted_selections)

        if not sum_of_counters_proof.is_valid(elgamal_accumulation, elgamal_public_key):
            # log warning already happened if this failed
            return False

        return True

    def decrypt(
        self,
        cd: ContestDescription,
        keypair: ElGamalKeyPair,
        suppress_validity_check: bool = False,
    ) -> Optional[PlaintextVotedContest]:
        """
        Given an encrypted contest, the contest description, and the ElGamal keypair which can decrypt it,
        returns the corresponding plaintext vote.

        :param cd: The contest description corresponding to `evc`
        :param keypair: Public and secret key for the election
        :param suppress_validity_check: If true, suppresses a validity check on the ciphertext
        :return a plaintext voted contest, if successful, or `None` if the encrypted voted contest is invalid
        """

        if not suppress_validity_check and not self.is_valid(cd, keypair.public_key):
            return None

        (
            contest_hash,
            encrypted_selections,
            zero_or_one_selection_proofs,
            sum_of_counters_proof,
        ) = self

        choices = [x.decrypt(keypair.secret_key) for x in encrypted_selections]

        return PlaintextVotedContest(contest_hash, choices)


# TODO: add a representation for write-in candidates.
#   Right now, we've just got a bit for a write-in candidate as an allowed possibility
#   in the Candidate class. We need a place for an encrypted string (symmetric-key?)
#   in EncryptedVotedContest, and we have to sort out how to manage that key, and avoid
#   leakage of information (so, constant-length ciphertext?).


def encrypt_voted_contest(
    pvc: PlaintextVotedContest,
    cd: ContestDescription,
    elgamal_public_key: ElementModP,
    seed: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[EncryptedVotedContest]:
    """
    Given a PlaintextVotedContext and the necessary key material, computes an encrypted
    version of the ballot, including all the necessary proofs.

    :param pvc: The plaintext voted contest
    :param cd: The contest description corresponding to `pvc`
    :param elgamal_public_key: Public key for the election
    :param seed: Nonce from which to derive other relevant nonces
    :param suppress_validity_check: If true, suppresses a validity check on the plaintext; only use this for testing!
    :return an encrypted voted contest, or `None` if the plaintext was invalid
    """
    if not suppress_validity_check and not pvc.is_valid(cd):
        return None

    num_slots = len(cd.ballot_selections)
    contest_hash = cd.crypto_hash()
    nonces = Nonces(seed, contest_hash)
    elgamal_nonces = nonces[0:num_slots]
    djcp_nonces = nonces[num_slots : num_slots * 2]
    ccp_nonce = nonces[num_slots * 2]

    ciphertexts: List[ElGamalCiphertext] = []
    zero_or_one_selection_proofs: List[DisjunctiveChaumPedersenProof] = []

    for i in range(0, num_slots):
        ciphertexts_i = elgamal_encrypt(
            pvc.choices[i], elgamal_nonces[i], elgamal_public_key
        )
        zp_i = flatmap_optional(
            ciphertexts_i,
            lambda c: make_disjunctive_chaum_pedersen(
                c, elgamal_nonces[i], elgamal_public_key, djcp_nonces[i], pvc.choices[i]
            ),
        )
        if ciphertexts_i is None or zp_i is None:
            return None
        else:
            ciphertexts.append(ciphertexts_i)
            zero_or_one_selection_proofs.append(zp_i)

    elgamal_accumulation = elgamal_add(*ciphertexts)
    sum_of_counters_proof = make_constant_chaum_pedersen(
        elgamal_accumulation,
        cd.number_elected,
        add_q(*elgamal_nonces),
        elgamal_public_key,
        ccp_nonce,
    )

    return flatmap_optional(
        sum_of_counters_proof,
        lambda p: EncryptedVotedContest(
            contest_hash, ciphertexts, zero_or_one_selection_proofs, p
        ),
    )
