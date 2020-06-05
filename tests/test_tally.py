import unittest
from datetime import timedelta
from typing import List, Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from electionguard.ballot import (
    BallotBoxState,
    CiphertextAcceptedBallot,
    from_ciphertext_ballot,
)
from electionguard.ballot_store import BallotStore

from electionguard.election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ, ONE_MOD_Q
from electionguard.tally import CiphertextTally, tally_ballots, tally_ballot

from electionguardtest.election import (
    election_descriptions,
    elections_and_ballots,
    ELECTIONS_AND_BALLOTS_TUPLE_TYPE,
)
from electionguardtest.group import elements_mod_q
from electionguardtest.tally import accumulate_plaintext_ballots


class TestTally(unittest.TestCase):
    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_cast_ballots_accumulates_valid_tally(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):
        # Arrange
        metadata, ballots, secret_key, context = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = BallotStore()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context)
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                from_ciphertext_ballot(encrypted_ballot, BallotBoxState.CAST),
            )

        # act
        result = tally_ballots(store, metadata, context)
        self.assertIsNotNone(result)

        # Assert
        decrypted_tallies = self._decrypt_with_secret(result, secret_key)
        self.assertEqual(plaintext_tallies, decrypted_tallies)

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_spoiled_ballots_accumulates_valid_tally(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):
        # Arrange
        metadata, ballots, secret_key, context = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = BallotStore()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context)
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                from_ciphertext_ballot(encrypted_ballot, BallotBoxState.SPOILED),
            )

        # act
        result = tally_ballots(store, metadata, context)
        self.assertIsNotNone(result)

        # Assert
        decrypted_tallies = self._decrypt_with_secret(result, secret_key)
        self.assertCountEqual(plaintext_tallies, decrypted_tallies)
        for value in decrypted_tallies.values():
            self.assertEqual(0, value)
        self.assertEqual(len(ballots), len(result.spoiled_ballots))

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_ballot_invalid_input_fails(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):

        # Arrange
        metadata, ballots, secret_key, context = everything

        # encrypt each ballot
        store = BallotStore()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context)
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                from_ciphertext_ballot(encrypted_ballot, BallotBoxState.CAST),
            )

        subject = CiphertextTally("my-tally", metadata, context)

        # act
        cached_ballots = store.all()
        first_ballot = cached_ballots[0]
        first_ballot.state = BallotBoxState.UNKNOWN

        # verify an UNKNOWN state ballot fails
        self.assertIsNone(tally_ballot(first_ballot, subject))
        self.assertFalse(subject.add_cast(first_ballot))
        self.assertFalse(subject.add_spoiled(first_ballot))

        # try to spoil a cast ballot
        first_ballot.state = BallotBoxState.CAST
        self.assertFalse(subject.add_spoiled(first_ballot))

        # try to cast a spoiled ballot
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(subject.add_cast(first_ballot))

        # reset to cast
        first_ballot.state = BallotBoxState.CAST

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                subject, first_ballot, BallotBoxState.CAST
            )
        )

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                subject, first_ballot, BallotBoxState.SPOILED
            )
        )

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                subject, first_ballot, BallotBoxState.UNKNOWN
            )
        )

        # verify a spoiled ballot cannot be added twice
        first_ballot.state = BallotBoxState.SPOILED
        self.assertTrue(subject.add_spoiled(first_ballot))
        self.assertFalse(subject.add_spoiled(first_ballot))

        # verify an already spoiled ballot cannot be cast
        first_ballot.state = BallotBoxState.CAST
        self.assertFalse(subject.add_cast(first_ballot))

        # pop the spoiled ballot
        subject.spoiled_ballots[first_ballot.object_id] = None

        # verify a cast ballot cannot be added twice
        first_ballot.state = BallotBoxState.CAST
        self.assertTrue(subject.add_cast(first_ballot))
        self.assertFalse(subject.add_cast(first_ballot))

        # verify an alraedy cast ballot cannot be spoiled
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(subject.add_spoiled(first_ballot))

    # def test_tally_ballot_already_spoiled_cannot_be_cast(self):

    def _decrypt_with_secret(
        self, tally: CiphertextTally, secret_key: ElementModQ
    ) -> Dict[str, int]:
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.cast.items():
            for object_id, selection in contest.tally_selections.items():
                plaintext = selection.message.decrypt(secret_key)
                plaintext_selections[object_id] = plaintext

        return plaintext_selections

    def _cannot_erroneously_mutate_state(
        self,
        subject: CiphertextTally,
        ballot: CiphertextAcceptedBallot,
        state_to_test: BallotBoxState,
    ) -> bool:

        input_state = ballot.state
        ballot.state = state_to_test

        # remove the first selection
        first_selection = ballot.contests[0].ballot_selections[0]
        ballot.contests[0].ballot_selections.remove(first_selection)
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.add_cast(ballot))
        self.assertFalse(subject.add_spoiled(ballot))

        ballot.contests[0].ballot_selections.insert(0, first_selection)

        # modify the contest description hash
        first_contest_hash = ballot.contests[0].description_hash
        ballot.contests[0].description_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.add_cast(ballot))
        self.assertFalse(subject.add_spoiled(ballot))

        ballot.contests[0].description_hash = first_contest_hash

        # modify a contest object id
        first_contest_object_id = ballot.contests[0].object_id
        ballot.contests[0].object_id = "a-bad-object-id"
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.add_cast(ballot))
        self.assertFalse(subject.add_spoiled(ballot))

        ballot.contests[0].object_id = first_contest_object_id

        # modify the ballot's hash
        first_ballot_hash = ballot.description_hash
        ballot.description_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.add_cast(ballot))
        self.assertFalse(subject.add_spoiled(ballot))

        ballot.description_hash = first_ballot_hash
        ballot.state = input_state

        return True
