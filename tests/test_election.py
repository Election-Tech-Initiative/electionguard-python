import unittest

import os
import jsons

from electionguard.election import Election

here = os.path.abspath(os.path.dirname(__file__))

class TestElection(unittest.TestCase):

    election_manifest_file_name = 'election_manifest.json'

    def test_election_can_deserialize(self):

        subject = self.__get_election_from_file(self.election_manifest_file_name)
        
        # print out the object if stdout is connected
        print(subject)

        self.assertIsNotNone(subject.election_scope_id)
        self.assertEquals(subject.election_scope_id, 'jefferson-county-primary')

    def test_election_is_valid(self):
        subject = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertTrue(subject.is_valid())

    def test_election_has_deterministic_hash(self):
        subject1 = self.__get_election_from_file(self.election_manifest_file_name)
        subject2 = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertEquals(subject1.crypto_hash(), subject2.crypto_hash())


    def __get_election_from_file(self, filename: str) -> Election:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = Election.from_json(data)

        return target

if __name__ == '__main__':
    unittest.main()