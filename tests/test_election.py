import unittest

from electionguard.election import ElectionDescription, InternalElectionDescription

import electionguardtest.election_factory as GENERATOR

factory = GENERATOR.ElectionFactory()


class TestElection(unittest.TestCase):
    def test_simple_election_is_valid(self):

        # Act
        subject = factory.get_simple_election_from_file()

        # Assert
        self.assertIsNotNone(subject.election_scope_id)
        self.assertEqual(subject.election_scope_id, "jefferson-county-primary")
        self.assertTrue(subject.is_valid())

    def test_simple_election_can_serialize(self):
        # Arrange
        subject = factory.get_simple_election_from_file()
        intermediate = subject.to_json()

        # Act
        result = ElectionDescription.from_json(intermediate)

        # Assert
        self.assertIsNotNone(result.election_scope_id)
        self.assertEqual(result.election_scope_id, "jefferson-county-primary")

    def test_election_has_deterministic_hash(self):

        # Act
        subject1 = factory.get_simple_election_from_file()
        subject2 = factory.get_simple_election_from_file()

        # Assert
        self.assertEqual(subject1.crypto_hash(), subject2.crypto_hash())

    def test_election_from_file_generates_consistent_internal_description_contest_hashes(
        self,
    ):
        # Arrange
        comparator = factory.get_simple_election_from_file()
        subject = InternalElectionDescription(comparator)

        self.assertEqual(len(comparator.contests), len(subject.contests))

        for expected in comparator.contests:
            for actual in subject.contests:
                if expected.object_id == actual.object_id:
                    self.assertEqual(expected.crypto_hash(), actual.crypto_hash())


if __name__ == "__main__":
    unittest.main()
