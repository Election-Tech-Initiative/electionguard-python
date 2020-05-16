import unittest

from hypothesis import given

from electionguard.election import ElectionDescription
from electionguardtest.election import arb_election_description


class TestContests(unittest.TestCase):
    def test_whatever(self):
        pass


class TestElections(unittest.TestCase):
    @given(arb_election_description())
    def test_generators_yield_valid_output(self, ed: ElectionDescription):
        self.assertTrue(ed.is_valid())
