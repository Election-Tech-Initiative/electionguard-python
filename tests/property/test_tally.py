from datetime import timedelta
from typing import Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from tests.base_test_case import BaseTestCase

from electionguard.ballot import (
    BallotBoxState,
    SubmittedBallot,
)
from electionguard.ballot_box import cast_ballot, spoil_ballot
from electionguard.data_store import DataStore
from electionguard.elgamal import ElGamalSecretKey
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ONE_MOD_Q
from electionguard.tally import CiphertextTally, tally_ballots, tally_ballot


from electionguard_tools.strategies.election import (
    elections_and_ballots,
    ElectionsAndBallotsTupleType,
)
from electionguard_tools.factories.election_factory import ElectionFactory
from electionguard_tools.helpers.tally_accumulate import accumulate_plaintext_ballots


class TestTally(BaseTestCase):
    """Tally tests"""

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=3,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(2, 5).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_cast_ballots_accumulates_valid_tally(
        self, everything: ElectionsAndBallotsTupleType
    ):
        # Arrange
        (
            _election_description,
            internal_manifest,
            ballots,
            secret_key,
            context,
        ) = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = DataStore()
        encryption_seed = ElectionFactory.get_encryption_device().get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(
                ballot,
                internal_manifest,
                context,
                encryption_seed,
                should_verify_proofs=True,
            )
            encryption_seed = encrypted_ballot.code
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                cast_ballot(encrypted_ballot),
            )

        # act
        result = tally_ballots(store, internal_manifest, context)
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
        self, everything: ElectionsAndBallotsTupleType
    ):
        # Arrange
        (
            _election_description,
            internal_manifest,
            ballots,
            secret_key,
            context,
        ) = everything
        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)

        # encrypt each ballot
        store = DataStore()
        encryption_seed = ElectionFactory.get_encryption_device().get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(
                ballot,
                internal_manifest,
                context,
                encryption_seed,
                should_verify_proofs=True,
            )
            encryption_seed = encrypted_ballot.code
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                spoil_ballot(encrypted_ballot),
            )

        # act
        tally = tally_ballots(store, internal_manifest, context)
        self.assertIsNotNone(tally)

        # Assert
        decrypted_tallies = self._decrypt_with_secret(tally, secret_key)
        self.assertCountEqual(plaintext_tallies, decrypted_tallies)
        for value in decrypted_tallies.values():
            self.assertEqual(0, value)
        self.assertEqual(len(ballots), tally.spoiled())

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=3,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(integers(1, 3).flatmap(lambda n: elections_and_ballots(n)))
    def test_tally_ballot_invalid_input_fails(
        self, everything: ElectionsAndBallotsTupleType
    ):

        # Arrange
        (
            _election_description,
            internal_manifest,
            ballots,
            _secret_key,
            context,
        ) = everything

        # encrypt each ballot
        store = DataStore()
        encryption_seed = ElectionFactory.get_encryption_device().get_hash()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(
                ballot, internal_manifest, context, encryption_seed
            )
            encryption_seed = encrypted_ballot.code
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                cast_ballot(encrypted_ballot),
            )

        tally = CiphertextTally("my-tally", internal_manifest, context)

        # act
        cached_ballots = store.all()
        first_ballot = cached_ballots[0]
        first_ballot.state = BallotBoxState.UNKNOWN

        # verify an UNKNOWN state ballot fails
        self.assertIsNone(tally_ballot(first_ballot, tally))
        self.assertFalse(tally.append(first_ballot, True))

        # cast a ballot
        first_ballot.state = BallotBoxState.CAST
        self.assertTrue(tally.append(first_ballot, False))

        # try to append a spoiled ballot
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(tally.append(first_ballot, True))

        # Verify accumulation fails if the selection collection is empty
        if first_ballot.state == BallotBoxState.CAST:
            self.assertFalse(
                tally.contests[first_ballot.object_id].accumulate_contest([])
            )

        # pop the cast ballot
        tally.cast_ballot_ids.pop()

        # reset to cast
        first_ballot.state = BallotBoxState.CAST

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                tally, first_ballot, BallotBoxState.CAST
            )
        )

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                tally, first_ballot, BallotBoxState.SPOILED
            )
        )

        self.assertTrue(
            self._cannot_erroneously_mutate_state(
                tally, first_ballot, BallotBoxState.UNKNOWN
            )
        )

        # verify a cast ballot cannot be added twice
        first_ballot.state = BallotBoxState.CAST
        self.assertTrue(tally.append(first_ballot, True))
        self.assertFalse(tally.append(first_ballot, False))

        # verify an already submitted ballot cannot be changed or readded
        first_ballot.state = BallotBoxState.SPOILED
        self.assertFalse(tally.append(first_ballot, True))

    @staticmethod
    def _decrypt_with_secret(
        tally: CiphertextTally, secret_key: ElGamalSecretKey
    ) -> Dict[str, int]:
        """
        Demonstrates how to decrypt a tally with a known secret key
        """
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.contests.items():
            for object_id, selection in contest.selections.items():
                plaintext_tally = selection.ciphertext.decrypt(secret_key)
                plaintext_selections[object_id] = plaintext_tally

        return plaintext_selections

    def _cannot_erroneously_mutate_state(
        self,
        tally: CiphertextTally,
        ballot: SubmittedBallot,
        state_to_test: BallotBoxState,
    ) -> bool:

        input_state = ballot.state
        ballot.state = state_to_test

        # remove the first selection
        first_contest = ballot.contests[0]
        first_selection = first_contest.ballot_selections[0]
        ballot.contests[0].ballot_selections.remove(first_selection)

        self.assertIsNone(tally_ballot(ballot, tally))
        self.assertFalse(tally.append(ballot, True))

        # Verify accumulation fails if the selection count does not match
        if ballot.state == BallotBoxState.CAST:
            first_tally = tally.contests[first_contest.object_id]
            self.assertFalse(
                first_tally.accumulate_contest(ballot.contests[0].ballot_selections)
            )

            # pylint: disable=protected-access
            _key, bad_accumulation = first_tally._accumulate_selections(
                first_selection.object_id,
                first_tally.selections[first_selection.object_id],
                ballot.contests[0].ballot_selections,
            )
            self.assertIsNone(bad_accumulation)

        ballot.contests[0].ballot_selections.insert(0, first_selection)

        # modify the contest description hash
        first_contest_hash = ballot.contests[0].description_hash
        ballot.contests[0].description_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, tally))
        self.assertFalse(tally.append(ballot, True))

        ballot.contests[0].description_hash = first_contest_hash

        # modify a contest object id
        first_contest_object_id = ballot.contests[0].object_id
        ballot.contests[0].object_id = "a-bad-object-id"
        self.assertIsNone(tally_ballot(ballot, tally))
        self.assertFalse(tally.append(ballot, True))

        ballot.contests[0].object_id = first_contest_object_id

        # modify a selection object id
        first_contest_selection_object_id = (
            ballot.contests[0].ballot_selections[0].object_id
        )
        ballot.contests[0].ballot_selections[0].object_id = "another-bad-object-id"

        self.assertIsNone(tally_ballot(ballot, tally))
        self.assertFalse(tally.append(ballot, True))

        # Verify accumulation fails if the selection object id does not match
        if ballot.state == BallotBoxState.CAST:
            self.assertFalse(
                tally.contests[ballot.contests[0].object_id].accumulate_contest(
                    ballot.contests[0].ballot_selections
                )
            )

        ballot.contests[0].ballot_selections[
            0
        ].object_id = first_contest_selection_object_id

        # modify the ballot's hash
        first_ballot_hash = ballot.manifest_hash
        ballot.manifest_hash = ONE_MOD_Q
        self.assertIsNone(tally_ballot(ballot, tally))
        self.assertFalse(tally.append(ballot, True))

        ballot.manifest_hash = first_ballot_hash
        ballot.state = input_state

        return True
