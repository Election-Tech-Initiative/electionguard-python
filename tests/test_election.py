import unittest

from electionguard.election import Election

import electionguardtest.election_factory as GENERATOR

factory = GENERATOR.ElectionFactory()

class TestElection(unittest.TestCase):

    def test_simple_election_is_valid(self):
        
        # Act
        subject = factory.get_simple_election_from_file()

        # Assert
        self.assertIsNotNone(subject.election_scope_id)
        self.assertEqual(subject.election_scope_id, 'jefferson-county-primary')
        self.assertTrue(subject.is_valid())

    def test_simple_election_can_serialize(self):
        # Arrange
        subject = factory.get_simple_election_from_file()
        intermediate = subject.to_json()

        # Act
        result = Election.from_json(intermediate)
        
        # Assert
        self.assertIsNotNone(result.election_scope_id)
        self.assertEqual(result.election_scope_id, 'jefferson-county-primary')

    def test_election_has_deterministic_hash(self):

        # Act
        subject1 = factory.get_simple_election_from_file()
        subject2 = factory.get_simple_election_from_file()

        # Assert
        self.assertEqual(subject1.crypto_hash(), subject2.crypto_hash())

if __name__ == '__main__':
    unittest.main()