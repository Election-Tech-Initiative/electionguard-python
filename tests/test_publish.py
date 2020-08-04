from datetime import datetime, timezone
from os import path
from shutil import rmtree
from unittest import TestCase

from electionguard.ballot import (
    PlaintextBallot,
    make_ciphertext_ballot,
)
from electionguard.decryption_mediator import PlaintextTally
from electionguard.election import (
    ElectionType,
    ElectionConstants,
    ElectionDescription,
    make_ciphertext_election_context,
)
from electionguard.group import ONE_MOD_Q, ONE_MOD_P, int_to_q_unchecked
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CoefficientValidationSet
from electionguard.publish import publish, publish_private_data, RESULTS_DIR
from electionguard.tally import CiphertextTally


class TestPublish(TestCase):
    def test_publish(self) -> None:
        # Arrange
        now = datetime.now(timezone.utc)
        description = ElectionDescription(
            "", ElectionType.unknown, now, now, [], [], [], [], [], []
        )
        context = make_ciphertext_election_context(1, 1, ONE_MOD_P, ONE_MOD_Q)
        constants = ElectionConstants()
        devices = []
        coefficients = [CoefficientValidationSet("", [], [])]
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

    def test_publish_private_data(self) -> None:
        # Arrange
        plaintext_ballots = [PlaintextBallot("", "", [])]
        encrypted_ballots = [
            make_ciphertext_ballot(
                "", "", int_to_q_unchecked(0), int_to_q_unchecked(0), []
            )
        ]
        guardians = [Guardian("", 1, 1, 1)]

        # Act
        publish_private_data(
            plaintext_ballots, encrypted_ballots, guardians,
        )

        # Assert
        self.assertTrue(path.exists(RESULTS_DIR))

        # Cleanup
        rmtree(RESULTS_DIR)
