import unittest
from datetime import timedelta
from typing import Tuple, List, Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from electionguard.ballot import PlaintextBallot, CiphertextBallot
from electionguard.decrypt import decrypt_ballot_with_secret
from electionguard.election import (
    ElectionDescription,
    InternalElectionDescription,
    CiphertextElectionContext,
)
from electionguard.elgamal import ElGamalCiphertext, elgamal_encrypt, elgamal_add
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ
from electionguard.nonces import Nonces
from electionguardtest.election import (
    arb_election_description,
    arb_election_and_ballots,
)
from electionguardtest.group import arb_element_mod_q


class TestElections(unittest.TestCase):
    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(arb_election_description())
    def test_generators_yield_valid_output(self, ed: ElectionDescription):
        # it's just a one-liner, but it exercises a ton of code to make sure all Hypothesis strategies work
        self.assertTrue(ed.is_valid())

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=5,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        integers(1, 3).flatmap(lambda n: arb_election_and_ballots(n)),
        arb_element_mod_q(),
    )
    def test_accumulation_encryption_decryption(
        self,
        everything: Tuple[
            InternalElectionDescription,
            List[PlaintextBallot],
            ElementModQ,
            CiphertextElectionContext,
        ],
        nonce: ElementModQ,
    ):
        ied, ballots, secret_key, ce = everything

        # - first up, we'll do a tally on the plaintext ballots
        # - next we'll encrypt the ballots
        # - then we'll do the homomorphic accumulation
        # - and decrypt the totals
        # - and we'd better get the same thing out

        counters = _accumulate_plaintext_ballots(ballots)
        num_ballots = len(ballots)
        num_contests = len(ied.contests)
        zero_nonce, *nonces = Nonces(nonce)[: num_ballots + 1]
        assert len(nonces) == num_ballots

        encrypted_zero = elgamal_encrypt(0, zero_nonce, ce.elgamal_public_key)

        c_ballots = []

        for i in range(num_ballots):
            cb = encrypt_ballot(ballots[i], ied, ce, nonces[i])
            c_ballots.append(cb)

            # before we do anything fancy, we'll decrypt each ballot and make sure that we get back
            # identical plaintext.

            self.assertIsNotNone(cb)
            self.assertEqual(num_contests, len(cb.contests))
            db = decrypt_ballot_with_secret(
                ballot=cb,
                election_metadata=ied,
                extended_base_hash=ce.crypto_extended_base_hash,
                public_key=ce.elgamal_public_key,
                secret_key=secret_key,
                remove_placeholders=True,
            )

            self.assertEqual(ballots[i], db)

        encrypted_totals = _accumulate_encrypted_ballots(encrypted_zero, c_ballots)

        decrypted_totals = {}
        for k in encrypted_totals.keys():
            decrypted_totals[k] = encrypted_totals[k].decrypt(secret_key)

        self.assertTrue(len(ied.contests) > 0)
        for contest in ied.contests:
            selections = contest.ballot_selections
            placeholders = contest.placeholder_selections
            self.assertTrue(len(selections) > 0)
            self.assertTrue(len(placeholders) > 0)

            decrypted_selection_counters = [
                decrypted_totals[k.object_id] for k in selections
            ]
            decrypted_placeholder_counters = [
                decrypted_totals[k.object_id] for k in placeholders
            ]
            plaintext_counters = [counters[k.object_id] for k in selections]

            self.assertEqual(decrypted_selection_counters, plaintext_counters)

            # validate the right number of selections including placeholders
            counter_sum = sum(decrypted_selection_counters)
            placeholder_sum = sum(decrypted_placeholder_counters)
            if contest.number_elected * num_ballots != counter_sum + placeholder_sum:
                print("Uh oh")

            self.assertEqual(
                contest.number_elected * num_ballots, counter_sum + placeholder_sum
            )


# TODO: expand this into a supported function in electionguard/encrypt.py
#   This should include generating Chaum-Pedersen decryption proofs over the ElGamal totals.
#   An interesting question is whether we want to squish everything back into
#   a single CiphertextBallot per ballot style, or what we want to do with
#   races that appear on more than one ballot style. The code below completely
#   blows off the concept of a specific ballot style and just focuses on the
#   better-be-unique selection object-ids.


def _accumulate_encrypted_ballots(
    encrypted_zero: ElGamalCiphertext, ballots: List[CiphertextBallot]
) -> Dict[str, ElGamalCiphertext]:
    counters: Dict[str, ElGamalCiphertext] = {}
    for b in ballots:
        for c in b.contests:
            for s in c.ballot_selections:
                desc_id = (
                    s.object_id
                )  # this should be the same as in the PlaintextBallot!
                if desc_id not in counters:
                    counters[desc_id] = encrypted_zero
                counters[desc_id] = elgamal_add(counters[desc_id], s.message)
    return counters


def _accumulate_plaintext_ballots(ballots: List[PlaintextBallot]) -> Dict[str, int]:
    counters: Dict[str, int] = {}
    for b in ballots:
        for c in b.contests:
            for s in c.ballot_selections:
                assert (
                    not s.is_placeholder_selection
                ), "we shouldn't have placeholder selections in the plaintext ballots"
                desc_id = s.object_id
                if desc_id not in counters:
                    counters[desc_id] = 0
                counters[
                    desc_id
                ] += s.to_int()  # returns 1 or 0 for n-of-m ballot selections
    return counters
