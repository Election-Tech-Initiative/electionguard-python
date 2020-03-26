from typing import NamedTuple, List

from electionguard.chaum_pedersen import DisjunctiveChaumPedersenProof, ConstantChaumPedersenProof, \
    make_constant_chaum_pedersen, \
    is_valid_disjunctive_chaum_pedersen, is_valid_constant_chaum_pedersen, make_disjunctive_chaum_pedersen
from electionguard.elgamal import ElGamalCiphertext, elgamal_encrypt, elgamal_add, ElGamalKeyPair, elgamal_decrypt
from electionguard.group import ElementModQ, ElementModP, add_q
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
    contest: ContestDescription
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

def make_contest_hash(c: ContestDescription) -> ElementModQ:
    """
    Given a ContestDescription, deterministically derives a "hash" of that contest,
    suitable for use in ElectionGuard's "base hash" values.
    """
    # We could just use str(c), but we want this to be easily reproducible outside Python
    candidate_hashes: List[str] = list(map(lambda s: "%s/%s/%s/%s" % (s.ballot_name,
                                                                      str(s.is_incumbent),
                                                                      str(s.is_dummy),
                                                                      str(s.is_writein)),
                                           c.ballot_selections))
    return hash_elems(c.abbreviation, c.ballot_title, c.ballot_subtitle, c.electoral_district_id, c.name,
                      str(c.number_elected), str(c.votes_allowed), *candidate_hashes)


def is_valid_plaintext_voted_contest(c: PlaintextVotedContest) -> bool:
    """
    Given a PlaintextVotedContest, validates that it's well-formed and suitable
    for encryption. Returns true if good, false if not. Also generates a log warning
    explaining what's wrong.
    """
    total = 0
    for choice in c.choices:
        if choice < 0 or choice > 1:
            log_warning("Currently only supporting choices of 0 or 1: %s" % str(c))
            return False
        total += choice

    if total != c.contest.number_elected:
        log_warning("Sum of choices doesn't match number_elected: %s" % str(c))
        return False

    if len(c.choices) != len(c.contest.ballot_selections) or len(c.choices) != c.contest.votes_allowed:
        log_warning("Number of choices in ContestDescription doesn't match PlaintextVotedContest: %s" % str(c))
        return False

    return True


def encrypt_voted_contest(c: PlaintextVotedContest, elgamal_public_key: ElementModP,
                          seed: ElementModQ, suppress_validity_check: bool = False) -> EncryptedVotedContest:
    """
    Given a PlaintextVotedContext and the necessary key material, computes an encrypted
    version of the ballot, including all the necessary proofs.
    :param c: The plaintext vote
    :param elgamal_public_key: Public key for the election
    :param seed: Nonce from which to derive other relevant nonces
    :param suppress_validity_check: If true, suppresses a validity check on the plaintext; only use this for testing!
    """
    if not suppress_validity_check and not is_valid_plaintext_voted_contest(c):
        raise Exception("Invalid PlaintextVotedContest")

    num_slots = len(c.contest.ballot_selections)
    contest_hash = make_contest_hash(c.contest)
    nonces = Nonces(seed, contest_hash)
    elgamal_nonces = nonces[0:num_slots]
    djcp_nonces = nonces[num_slots:num_slots * 2]
    ccp_nonce = nonces[num_slots * 2]

    ciphertexts: List[ElGamalCiphertext] = []
    zero_or_one_selection_proofs: List[DisjunctiveChaumPedersenProof] = []

    for i in range(0, num_slots):
        ciphertexts_i = elgamal_encrypt(c.choices[i], elgamal_nonces[i], elgamal_public_key)
        ciphertexts.append(ciphertexts_i)
        zp_i = make_disjunctive_chaum_pedersen(ciphertexts_i, elgamal_nonces[i], elgamal_public_key, djcp_nonces[i], c.choices[i])
        zero_or_one_selection_proofs.append(zp_i)

    elgamal_accumulation = elgamal_add(*ciphertexts)
    sum_of_counters_proof = make_constant_chaum_pedersen(elgamal_accumulation, c.contest.number_elected,
                                                         add_q(*elgamal_nonces), elgamal_public_key, ccp_nonce)

    return EncryptedVotedContest(contest_hash, ciphertexts, zero_or_one_selection_proofs, sum_of_counters_proof)


def decrypt_voted_contest(e: EncryptedVotedContest, d: ContestDescription,
                          keypair: ElGamalKeyPair) -> PlaintextVotedContest:
    """
    Given an encrypted contest, the contest description, and the ElGamal keypair which can decrypt it,
    returns the corresponding plaintext vote. If you want to validate the proofs first, use
    `is_valid_encrypted_voted_contest`.
    """

    contest_hash, encrypted_selections, zero_or_one_selection_proofs, sum_of_counters_proof = e
    choices: List[int] = list(map(lambda x: elgamal_decrypt(x, keypair.secret_key), encrypted_selections))
    return PlaintextVotedContest(d, choices)


def is_valid_encrypted_voted_contest(e: EncryptedVotedContest, d: ContestDescription,
                                     elgamal_public_key: ElementModP) -> bool:
    """
    Given an EncryptedVotedContest and the corresponding ContestDescription
    and ElGamal public key, validates all the proofs. Returns
    true if everything is good, false otherwise and logs a warning.
    """

    contest_hash, encrypted_selections, zero_or_one_selection_proofs, sum_of_counters_proof = e

    num_slots = len(d.ballot_selections)
    if len(encrypted_selections) != num_slots:
        log_warning("expected %d encrypted ballots, got %d: %s" % (num_slots, len(encrypted_selections), str(e)))
        return False

    if len(zero_or_one_selection_proofs) != num_slots:
        log_warning("expected %d disjunctive Chaum-Pedersen proofs, got %d: %s" %
                    (num_slots, len(zero_or_one_selection_proofs), str(e)))
        return False

    if contest_hash != make_contest_hash(d):
        log_warning("contest_hash %s doesn't match %s: %s" %
                    (str(contest_hash), str(make_contest_hash(d)), str(e)))
        return False

    for i in range(0, num_slots):
        if encrypted_selections[i] != zero_or_one_selection_proofs[i].message:
            log_warning("ElGamal ciphertext #%d doesn't match the Chaum-Pedersen proof: %s" % (i, str(e)))
            return False
        if not is_valid_disjunctive_chaum_pedersen(zero_or_one_selection_proofs[i], elgamal_public_key):
            # log warning already happened if this failed
            return False

    elgamal_accumulation = elgamal_add(*encrypted_selections)
    if elgamal_accumulation != e.sum_of_counters_proof.message:
        log_warning("ElGamal accumulation ciphertext doesn't match the Chaum-Pedersen proof: %s" % str(e))
        return False

    if not is_valid_constant_chaum_pedersen(sum_of_counters_proof, elgamal_public_key):
        # log warning already happened if this failed
        return False

    return True
