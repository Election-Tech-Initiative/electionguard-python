from typing import NamedTuple, List, Optional

from electionguard.chaum_pedersen import (
    DisjunctiveChaumPedersenProof,
    ConstantChaumPedersenProof,
    make_constant_chaum_pedersen,
    is_valid_disjunctive_chaum_pedersen,
    is_valid_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
)
from electionguard.elgamal import (
    ElGamalCiphertext,
    elgamal_encrypt,
    elgamal_add,
    ElGamalKeyPair,
    elgamal_decrypt,
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


class PlaintextVotedContest(NamedTuple):
    contest_hash: ElementModQ  # derived from a ContestDescription
    choices: List[int]
    # For the choices, 0 = no vote, 1 = vote, 2+ = reserved for RCV and such later on
    # And the indices into this list are the same as the indices into the ballot_selections


class EncryptedVotedContest(NamedTuple):
    contest_hash: ElementModQ  # derived from a ContestDescription
    encrypted_selections: List[ElGamalCiphertext]
    zero_or_one_selection_proofs: List[DisjunctiveChaumPedersenProof]
    sum_of_counters_proof: ConstantChaumPedersenProof


# TODO: add a representation for write-in candidates.
#   Right now, we've just got a bit for a write-in candidate as an allowed possibility
#   in the Candidate class. We need a place for an encrypted string (symmetric-key?)
#   in EncryptedVotedContest, and we have to sort out how to manage that key, and avoid
#   leakage of information (so, constant-length ciphertext?).


def make_contest_hash(cd: ContestDescription) -> ElementModQ:
    """
    Given a ContestDescription, deterministically derives a "hash" of that contest,
    suitable for use in ElectionGuard's "base hash" values, and for validating that
    either a plaintext or encrypted voted context and its corresponding contest
    description match up.
    """
    # We could just use str(cd), but we want this to be easily reproducible outside Python
    candidate_hashes: List[str] = list(
        map(
            lambda s: f"({s.ballot_name}/{str(s.is_incumbent)}/{str(s.is_dummy)}/{str(s.is_writein)})",
            cd.ballot_selections,
        )
    )
    return hash_elems(
        cd.abbreviation,
        cd.ballot_title,
        cd.ballot_subtitle,
        cd.electoral_district_id,
        cd.name,
        str(cd.number_elected),
        str(cd.votes_allowed),
        *candidate_hashes,
    )


def is_valid_plaintext_voted_contest(
    pvc: PlaintextVotedContest, cd: ContestDescription
) -> bool:
    """
    Given a PlaintextVotedContest and its corresponding ContestDescription, validates
    that the plaintext well-formed and suitable for encryption. Returns true if good,
    false if not. Also generates a log warning explaining what's wrong.
    """
    h = make_contest_hash(cd)
    if h != pvc.contest_hash:
        log_warning(
            f"mismatching contest hash: plaintext({str(pvc)}), contest description({str(cd)})"
        )
        return False

    total = 0
    for choice in pvc.choices:
        if choice < 0 or choice > 1:
            log_warning(f"Currently only supporting choices of 0 or 1: {str(pvc)}")
            return False
        total += choice

    if total != cd.number_elected:
        log_warning(f"Sum of choices doesn't match number_elected: {str(pvc)}")
        return False

    if (
        len(pvc.choices) != len(cd.ballot_selections)
        or len(pvc.choices) != cd.votes_allowed
    ):
        log_warning(
            f"Number of choices in ContestDescription doesn't match PlaintextVotedContest: {str(pvc)}"
        )
        return False

    return True


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
    if not suppress_validity_check and not is_valid_plaintext_voted_contest(pvc, cd):
        return None

    num_slots = len(cd.ballot_selections)
    contest_hash = make_contest_hash(cd)
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


def decrypt_voted_contest(
    evc: EncryptedVotedContest,
    cd: ContestDescription,
    keypair: ElGamalKeyPair,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextVotedContest]:
    """
    Given an encrypted contest, the contest description, and the ElGamal keypair which can decrypt it,
    returns the corresponding plaintext vote.

    :param evc: The encrypted voted contest
    :param cd: The contest description corresponding to `evc`
    :param keypair: Public and secret key for the election
    :param suppress_validity_check: If true, suppresses a validity check on the ciphertext
    :return a plaintext voted contest, if successful, or `None` if the encrypted voted contest is invalid
    """

    if not suppress_validity_check and not is_valid_encrypted_voted_contest(
        evc, cd, keypair.public_key
    ):
        return None

    (
        contest_hash,
        encrypted_selections,
        zero_or_one_selection_proofs,
        sum_of_counters_proof,
    ) = evc

    choices: List[int] = list(
        map(lambda x: elgamal_decrypt(x, keypair.secret_key), encrypted_selections)
    )
    return PlaintextVotedContest(contest_hash, choices)


def is_valid_encrypted_voted_contest(
    evc: EncryptedVotedContest, cd: ContestDescription, elgamal_public_key: ElementModP
) -> bool:
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
    ) = evc

    if make_contest_hash(cd) != contest_hash:
        log_warning(f"mismatching contest hashes, evc({str(evc)}), cd({str(cd)})")
        return False

    num_slots = len(cd.ballot_selections)
    if len(encrypted_selections) != num_slots:
        log_warning(
            f"expected {num_slots} encrypted ballots, got {len(encrypted_selections)}: {str(evc)}"
        )
        return False

    if len(zero_or_one_selection_proofs) != num_slots:
        log_warning(
            f"expected {num_slots} disjunctive Chaum-Pedersen proofs, got {len(zero_or_one_selection_proofs)}: {str(evc)}"
        )
        return False

    for i in range(0, num_slots):
        if not is_valid_disjunctive_chaum_pedersen(
            encrypted_selections[i], zero_or_one_selection_proofs[i], elgamal_public_key
        ):
            # log warning already happened if this failed
            return False

    elgamal_accumulation = elgamal_add(*encrypted_selections)

    if not is_valid_constant_chaum_pedersen(
        elgamal_accumulation, sum_of_counters_proof, elgamal_public_key
    ):
        # log warning already happened if this failed
        return False

    return True
