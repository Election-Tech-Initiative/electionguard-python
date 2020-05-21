import unittest
from datetime import timedelta
from typing import Tuple, List

from hypothesis import given, HealthCheck, settings

from electionguard.ballot import PlaintextBallot
from electionguard.election import (
    ElectionDescription,
    InternalElectionDescription,
    CiphertextElection,
)
from electionguard.group import ElementModQ
from electionguardtest.election import (
    arb_election_description,
    arb_election_and_ballots,
    arb_ciphertext_election,
)


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

    @given(arb_election_and_ballots(), arb_ciphertext_election())
    def test_accumulation_encryption_decryption(
        self,
        input: Tuple[InternalElectionDescription, List[PlaintextBallot]],
        context: Tuple[ElementModQ, CiphertextElection],
    ):
        ied, ballots = input
        secret_key, ce = context

        # - first up, we'll do a tally on the plaintext ballots
        # - next we'll encrypt the ballots
        # - then we'll do the homomorphic accumulation
        # - and decrypt the totals
        # - and we'd better get the same thing out
