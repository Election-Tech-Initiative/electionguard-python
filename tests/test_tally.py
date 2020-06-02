import unittest
from datetime import timedelta
from typing import List, Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from electionguard.ballot_store import (
    BallotBoxCiphertextBallot,
    BallotBoxState,
    BallotStore,
    from_ciphertext_ballot,
)

from electionguard.election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ
from electionguard.tally import CiphertextTally, tally_ballots

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
    def test_tally_ballots_accumulates_valid_tally(
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

    def test_tally_ballot_invalid_input_fails(self):

        # verify an unknown state ballot fails

        # verify adding a malformed cast ballot fails

        # verify adding a malformed spopiled ballot fails
        pass

    def _decrypt_with_secret(
        self, tally: CiphertextTally, secret_key: ElementModQ
    ) -> Dict[str, int]:
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.cast.items():
            for object_id, selection in contest.tally_selections.items():
                plaintext = selection.message.decrypt(secret_key)
                plaintext_selections[object_id] = plaintext

        return plaintext_selections
