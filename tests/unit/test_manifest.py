from datetime import datetime

from tests.base_test_case import BaseTestCase

from electionguard.manifest import (
    ContestDescriptionWithPlaceholders,
    Manifest,
    InternalManifest,
    SelectionDescription,
    VoteVariationType,
)
import electionguard_tools.factories.election_factory as ElectionFactory
import electionguard_tools.factories.ballot_factory as BallotFactory
from electionguard_tools.helpers.serialize import from_raw, to_raw

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestManifest(BaseTestCase):
    """Manifest tests"""

    def test_simple_manifest_is_valid(self):

        # Act
        subject = election_factory.get_simple_manifest_from_file()

        # Assert
        self.assertIsNotNone(subject.election_scope_id)
        self.assertEqual(subject.election_scope_id, "jefferson-county-primary")
        self.assertTrue(subject.is_valid())

    def test_simple_manifest_can_serialize(self):
        # Arrange
        subject = election_factory.get_simple_manifest_from_file()
        intermediate = to_raw(subject)

        # Act
        result = from_raw(Manifest, intermediate)

        # Assert
        self.assertIsNotNone(result.election_scope_id)
        self.assertEqual(result.election_scope_id, "jefferson-county-primary")

    def test_manifest_has_deterministic_hash(self):

        # Act
        subject1 = election_factory.get_simple_manifest_from_file()
        subject2 = election_factory.get_simple_manifest_from_file()

        # Assert
        self.assertEqual(subject1.crypto_hash(), subject2.crypto_hash())

    def test_manifest_hash_is_consistent_regardless_of_format(self):

        # Act
        subject1 = election_factory.get_simple_manifest_from_file()
        subject1.start_date = from_raw(datetime, '"2020-03-01T08:00:00-05:00"')

        subject2 = election_factory.get_simple_manifest_from_file()
        subject2.start_date = from_raw(datetime, '"2020-03-01T13:00:00-00:00"')

        subject3 = election_factory.get_simple_manifest_from_file()
        subject3.start_date = from_raw(datetime, '"2020-03-01T13:00:00.000-00:00"')

        subjects = [subject1, subject2, subject3]

        # Assert
        hashes = [subject.crypto_hash() for subject in subjects]
        for other_hash in hashes[1:]:
            self.assertEqual(hashes[0], other_hash)

    def test_manifest_from_file_generates_consistent_internal_description_contest_hashes(
        self,
    ):
        # Arrange
        comparator = election_factory.get_simple_manifest_from_file()
        subject = InternalManifest(comparator)

        self.assertEqual(len(comparator.contests), len(subject.contests))

        for expected in comparator.contests:
            for actual in subject.contests:
                if expected.object_id == actual.object_id:
                    self.assertEqual(expected.crypto_hash(), actual.crypto_hash())

    def test_contest_description_valid_input_succeeds(self):
        description = ContestDescriptionWithPlaceholders(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    "0@A.com-selection",
                    0,
                    "0@A.com",
                ),
                SelectionDescription(
                    "0@B.com-selection",
                    1,
                    "0@B.com",
                ),
            ],
            ballot_title=None,
            ballot_subtitle=None,
            placeholder_selections=[
                SelectionDescription(
                    "0@A.com-contest-2-placeholder",
                    2,
                    "0@A.com-contest-2-candidate",
                )
            ],
        )

        self.assertTrue(description.is_valid())

    def test_contest_description_invalid_input_fails(self):

        description = ContestDescriptionWithPlaceholders(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    "0@A.com-selection",
                    0,
                    "0@A.com",
                ),
                # simulate a bad selection description input
                SelectionDescription(
                    "0@A.com-selection",
                    1,
                    "0@A.com",
                ),
            ],
            ballot_title=None,
            ballot_subtitle=None,
            placeholder_selections=[
                SelectionDescription(
                    "0@A.com-contest-2-placeholder",
                    2,
                    "0@A.com-contest-2-candidate",
                )
            ],
        )

        self.assertFalse(description.is_valid())
