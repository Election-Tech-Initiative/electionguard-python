from datetime import datetime, timezone
from os import path
from shutil import rmtree
from tests.base_test_case import BaseTestCase

from electionguard.ballot import (
    PlaintextBallot,
    make_ciphertext_ballot,
)
from electionguard.constants import ElectionConstants
from electionguard.election import make_ciphertext_election_context
from electionguard.group import ONE_MOD_Q, ONE_MOD_P, int_to_q_unchecked
from electionguard.guardian import GuardianRecord
from electionguard.manifest import ElectionType, Manifest
from electionguard.publish import publish, publish_private_data, RESULTS_DIR
from electionguard.tally import (
    CiphertextTally,
    PlaintextTally,
)


class TestPublish(BaseTestCase):
    """Publishing tests"""

    def test_publish(self) -> None:
        # Arrange
        now = datetime.now(timezone.utc)
        manifest = Manifest("", ElectionType.unknown, now, now, [], [], [], [], [], [])
        context = make_ciphertext_election_context(
            1, 1, ONE_MOD_P, ONE_MOD_Q, ONE_MOD_Q
        )
        constants = ElectionConstants(1, 1, 1, 1)
        devices = []
        guardian_records = [GuardianRecord("", "", ONE_MOD_Q, [], [])]
        encrypted_ballots = []
        spoiled_ballots = []
        plaintext_tally = PlaintextTally("", [])
        ciphertext_tally = CiphertextTally("", manifest, context)

        # Act
        publish(
            manifest,
            context,
            constants,
            devices,
            encrypted_ballots,
            spoiled_ballots,
            ciphertext_tally.publish(),
            plaintext_tally,
            guardian_records,
        )

        # Assert
        self.assertTrue(path.exists(RESULTS_DIR))

        # Cleanup
        rmtree(RESULTS_DIR)

    def test_publish_private_data(self) -> None:
        # Arrange
        plaintext_ballots = [PlaintextBallot("", "", [])]
        encrypted_ballots = [
            make_ciphertext_ballot(
                "", "", int_to_q_unchecked(0), int_to_q_unchecked(0), []
            )
        ]
        guardian_records = [GuardianRecord("", "", ONE_MOD_Q, [], [])]

        # Act
        publish_private_data(
            plaintext_ballots,
            encrypted_ballots,
            guardian_records,
        )

        # Assert
        self.assertTrue(path.exists(RESULTS_DIR))

        # Cleanup
        rmtree(RESULTS_DIR)
