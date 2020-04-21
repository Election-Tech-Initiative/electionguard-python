import unittest

import os

from electionguard.election import Election

here = os.path.abspath(os.path.dirname(__file__))

class TestElection(unittest.TestCase):

    election_manifest_file_name = 'election_manifest.json'

    def test_election_can_deserialize(self):

        subject = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertIsNotNone(subject.election_scope_id)
        self.assertEqual(subject.election_scope_id, 'jefferson-county-primary')

    def test_election_can_serialize(self):

        subject = self.__get_election_from_file(self.election_manifest_file_name)

        intermediate = subject.to_json()

        print(intermediate)

        result = Election.from_json(intermediate)
        
        self.assertIsNotNone(result.election_scope_id)
        self.assertEqual(result.election_scope_id, 'jefferson-county-primary')

    def test_election_is_valid(self):
        subject = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertTrue(subject.is_valid())

    def test_election_has_deterministic_hash(self):
        subject1 = self.__get_election_from_file(self.election_manifest_file_name)
        subject2 = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertEqual(subject1.crypto_hash(), subject2.crypto_hash())


    def __get_election_from_file(self, filename: str) -> Election:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = Election.from_json(data)

        return target

if __name__ == '__main__':
    unittest.main()