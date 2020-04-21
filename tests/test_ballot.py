import unittest
import os
from typing import Tuple

from datetime import timedelta

from hypothesis import HealthCheck
from hypothesis import given, settings


from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotSelection
)

import electionguardtest.ballot_factory as GENERATOR

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

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        GENERATOR.get_selection_well_formed()
    )
    def test_plaintext_ballot_selection_is_valid(self, subject: Tuple[str, PlaintextBallotSelection]):
        # Arrange
        object_id, selection = subject

        # Act
        as_int = selection.to_int()
        is_valid = selection.is_valid(object_id)

        # Assert
        self.assertTrue(is_valid)
        self.assertTrue(as_int >= 0 and as_int <= 1)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        GENERATOR.get_selection_poorly_formed()
    )
    def test_plaintext_ballot_selection_is_invalid(self, subject: Tuple[str, PlaintextBallotSelection]):
        # Arrange
        object_id, selection = subject
        a_different_object_id = f"{object_id}-not-the-same"

        # Act
        as_int = selection.to_int()
        is_valid = selection.is_valid(a_different_object_id)

        # Assert
        self.assertFalse(is_valid)
        self.assertTrue(as_int >= 0 and as_int <= 1)


    def __get_ballot_from_file(self, filename: str) -> PlaintextBallot:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = PlaintextBallot.from_json(data)

        return target

if __name__ == '__main__':
    unittest.main()