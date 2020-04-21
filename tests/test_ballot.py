import unittest

import os
import jsons

from electionguard.ballot import PlaintextBallot

here = os.path.abspath(os.path.dirname(__file__))

class TestBallot(unittest.TestCase):

    ballot_in_file_name = 'ballot_in.json'

    def test_election_can_deserialize(self):

        with open(os.path.join(here, 'data', self.ballot_in_file_name), 'r') as subject:
            data = subject.read()
            target = PlaintextBallot.from_json(data)
        
        # print out the object if stdout is connected
        print(target)

        self.assertIsNotNone(target.object_id)
        self.assertEqual(target.object_id, 'some-external-id-string-123')


    def test_ballot_is_valid(self):
        subject = self.__get_ballot_from_file(self.ballot_in_file_name)

        self.assertTrue(subject.is_valid("jefferson-county"))

    def test_ballot_can_encrypt(self):
        pass


    def __get_ballot_from_file(self, filename: str) -> PlaintextBallot:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = PlaintextBallot.from_json(data)

        return target

if __name__ == '__main__':
    unittest.main()