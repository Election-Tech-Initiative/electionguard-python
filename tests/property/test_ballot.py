from typing import Tuple
from datetime import timedelta
from hypothesis import HealthCheck
from hypothesis import given, settings

from tests.base_test_case import BaseTestCase

from electionguard.ballot import PlaintextBallotSelection

import electionguard_tools.factories.ballot_factory as BallotFactory


class TestBallot(BaseTestCase):
    """Ballot tests"""

    def test_ballot_is_valid(self):
        # Arrange
        factory = BallotFactory.BallotFactory()

        # Act
        subject = factory.get_simple_ballot_from_file()
        first_contest = subject.contests[0]
        self.assertIsNotNone(first_contest)

        # Assert
        self.assertIsNotNone(subject.object_id)
        self.assertEqual(subject.object_id, "some-external-id-string-123")
        self.assertTrue(subject.is_valid("jefferson-county-ballot-style"))
        self.assertTrue(first_contest.is_valid("justice-supreme-court", 2, 2))
        self.assertFalse(first_contest.is_valid("some-other-contest", 2, 2))
        self.assertFalse(first_contest.is_valid("justice-supreme-court", 1, 2))
        self.assertFalse(first_contest.is_valid("justice-supreme-court", 2, 1))
        self.assertFalse(first_contest.is_valid("justice-supreme-court", 2, 2, 1))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(BallotFactory.get_selection_well_formed())
    def test_plaintext_ballot_selection_is_valid(
        self, subject: Tuple[str, PlaintextBallotSelection]
    ):
        # Arrange
        object_id, selection = subject

        # Act
        as_int = selection.vote
        is_valid = selection.is_valid(object_id)

        # Assert
        self.assertTrue(is_valid)
        self.assertTrue(0 <= as_int <= 1)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(BallotFactory.get_selection_poorly_formed())
    def test_plaintext_ballot_selection_is_invalid(
        self, subject: Tuple[str, PlaintextBallotSelection]
    ):
        # Arrange
        object_id, selection = subject
        a_different_object_id = f"{object_id}-not-the-same"

        # Act
        as_int = selection.vote
        is_valid = selection.is_valid(a_different_object_id)

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(0 <= as_int <= 1)
