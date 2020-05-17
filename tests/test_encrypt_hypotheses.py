import unittest
from datetime import timedelta

from hypothesis import given, HealthCheck, settings

from electionguard.election import ElectionDescription
from electionguardtest.election import arb_election_description


class TestContests(unittest.TestCase):
    def test_whatever(self):
        pass


class TestElections(unittest.TestCase):
    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(arb_election_description())
    def test_generators_yield_valid_output(self, ed: ElectionDescription):
        self.assertTrue(ed.is_valid())
