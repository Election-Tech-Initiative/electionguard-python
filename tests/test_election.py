import unittest

import os
import jsons

from electionguard.election import Election

here = os.path.abspath(os.path.dirname(__file__))

class TestElection(unittest.TestCase):

    election_manifest_file_name = 'election_manifest.json'

    def test_election_can_deserialize(self):

        with open(os.path.join(here, 'data', 'election_manifest.json'), 'r') as subject:
            data = subject.read()
            target = Election.from_json(data)
        
        # print out the object if stdout is connected
        print(target)

        self.assertIsNotNone(target.election_scope_id)
        self.assertEquals(target.election_scope_id, 'jefferson-county-primary')

    def test_election_is_valid(self):
        subject = self.__get_election_from_file(self.election_manifest_file_name)

        self.assertTrue(subject.is_valid())

    def test_election_is_invalid(self):
        # TODO:
        pass


    def __get_election_from_file(self, filename: str) -> Election:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = Election.from_json(data)

        return target

if __name__ == '__main__':
    unittest.main()