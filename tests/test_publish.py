from os import path
from shutil import rmtree
from unittest import TestCase
from datetime import datetime, timezone

from electionguard.decryption_mediator import PlaintextTally
from electionguard.election import (
    ElectionType,
    CiphertextElectionContext,
    ElectionConstants,
    ElectionDescription,
)
from electionguard.tally import CiphertextTally

from electionguard.publish import publish, RESULTS_DIR

from electionguard.group import ONE_MOD_Q, ONE_MOD_P


class TestPublish(TestCase):
    def test_publish(self) -> None:
        # Arrange
        now = datetime.now(timezone.utc)
        description = ElectionDescription(
            "", ElectionType.unknown, now, now, [], [], [], [], [], []
        )
        context = CiphertextElectionContext(1, 1, ONE_MOD_P, ONE_MOD_Q)
        constants = ElectionConstants()
        devices = []
        coefficients = []
        encrypted_ballots = []
        tally = PlaintextTally("", [], [])

        # Act
        publish(
            description,
            context,
            constants,
            devices,
            encrypted_ballots,
            CiphertextTally("", description, context),
            tally,
            coefficients,
        )

        # Assert
        self.assertTrue(path.exists(RESULTS_DIR))

        # Cleanup
        rmtree(RESULTS_DIR)
