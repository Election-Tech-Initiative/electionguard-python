from unittest import TestCase
from datetime import timedelta
from typing import Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from electionguard.ballot import (
    BallotBoxState,
    CiphertextAcceptedBallot,
    from_ciphertext_ballot,
)
from electionguard.ballot_store import BallotStore

from electionguard.encrypt import encrypt_ballot, EncryptionDevice
from electionguard.group import ElementModQ, ONE_MOD_Q
from electionguard.tally import CiphertextTally, tally_ballots, tally_ballot

from electionguardtest.election import (
    elections_and_ballots,
    ELECTIONS_AND_BALLOTS_TUPLE_TYPE,
)
from electionguardtest.tally import accumulate_plaintext_ballots


class TestTally(TestCase):
    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=3,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(2, 5).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_cast_ballots_accumulates_valid_tally(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):
        # Arrange
        election_description, metadata, ballots, secret_key, context = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = BallotStore()
        seed_hash = EncryptionDevice("Location").get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context, seed_hash)
            seed_hash = encrypted_ballot.tracking_hash
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
        max_examples=3,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_spoiled_ballots_accumulates_valid_tally(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):
        # Arrange
        election_description, metadata, ballots, secret_key, context = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = BallotStore()
        seed_hash = EncryptionDevice("Location").get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context, seed_hash)
            seed_hash = encrypted_ballot.tracking_hash
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
        max_examples=3,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_ballot_invalid_input_fails(
        self, everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE
    ):

        # Arrange
        election_description, metadata, ballots, secret_key, context = everything

        # encrypt each ballot
        store = BallotStore()
        seed_hash = EncryptionDevice("Location").get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(ballot, metadata, context, seed_hash)
            seed_hash = encrypted_ballot.tracking_hash
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
        self.assertFalse(subject.append(first_ballot))

        # cast a ballot
        first_ballot.state = BallotBoxState.CAST
        self.assertTrue(subject.append(first_ballot))

        # try to append a spoiled ballot
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(subject.append(first_ballot))

        # Verify accumulation fails if the selection collection is empty
        if first_ballot.state == BallotBoxState.CAST:
            self.assertFalse(
                subject.cast[first_ballot.object_id].accumulate_contest([])
            )

        # pop the cast ballot
        subject._cast_ballot_ids.pop()

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
        self.assertTrue(subject.append(first_ballot))
        self.assertFalse(subject.append(first_ballot))

        # verify an already spoiled ballot cannot be cast
        first_ballot.state = BallotBoxState.CAST
        self.assertFalse(subject.append(first_ballot))

        # pop the spoiled ballot
        subject.spoiled_ballots.pop(first_ballot.object_id)

        # verify a cast ballot cannot be added twice
        first_ballot.state = BallotBoxState.CAST
        self.assertTrue(subject.append(first_ballot))
        self.assertFalse(subject.append(first_ballot))

        # verify an already cast ballot cannot be spoiled
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(subject.append(first_ballot))

    def _decrypt_with_secret(
        self, tally: CiphertextTally, secret_key: ElementModQ
    ) -> Dict[str, int]:
        """
        Demonstrates how to decrypt a tally with a known secret key
        """
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.cast.items():
            for object_id, selection in contest.tally_selections.items():
                plaintext_tally = selection.ciphertext.decrypt(secret_key)
                plaintext_selections[object_id] = plaintext_tally

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
        first_contest = ballot.contests[0]
        first_selection = first_contest.ballot_selections[0]
        ballot.contests[0].ballot_selections.remove(first_selection)

        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.append(ballot))

        # Verify accumulation fails if the selection count does not match
        if ballot.state == BallotBoxState.CAST:
            first_tally = subject.cast[first_contest.object_id]
            self.assertFalse(
                first_tally.accumulate_contest(ballot.contests[0].ballot_selections)
            )

            key, bad_accumulation = first_tally._accumulate_selections(
                first_selection.object_id,
                first_tally.tally_selections[first_selection.object_id],
                ballot.contests[0].ballot_selections,
            )
            self.assertIsNone(bad_accumulation)

        ballot.contests[0].ballot_selections.insert(0, first_selection)

        # modify the contest description hash
        first_contest_hash = ballot.contests[0].description_hash
        ballot.contests[0].description_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.append(ballot))

        ballot.contests[0].description_hash = first_contest_hash

        # modify a contest object id
        first_contest_object_id = ballot.contests[0].object_id
        ballot.contests[0].object_id = "a-bad-object-id"
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.append(ballot))

        ballot.contests[0].object_id = first_contest_object_id

        # modify a selection object id
        first_contest_selection_object_id = (
            ballot.contests[0].ballot_selections[0].object_id
        )
        ballot.contests[0].ballot_selections[0].object_id = "another-bad-object-id"

        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.append(ballot))

        # Verify accumulation fails if the selection object id does not match
        if ballot.state == BallotBoxState.CAST:
            self.assertFalse(
                subject.cast[ballot.contests[0].object_id].accumulate_contest(
                    ballot.contests[0].ballot_selections
                )
            )

        ballot.contests[0].ballot_selections[
            0
        ].object_id = first_contest_selection_object_id

        # modify the ballot's hash
        first_ballot_hash = ballot.description_hash
        ballot.description_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, subject))
        self.assertFalse(subject.append(ballot))

        ballot.description_hash = first_ballot_hash
        ballot.state = input_state

        return True
