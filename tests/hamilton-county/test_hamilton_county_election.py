import unittest

from electionguard.election import (
    ContestDescriptionWithPlaceholders,
    ElectionDescription,
    InternalElectionDescription,
    SelectionDescription,
    VoteVariationType,
)
import electionguardtest.election_factory as ElectionFactory
import electionguardtest.ballot_factory as BallotFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestHamiltonCountyElection(unittest.TestCase):
    """
    Demonstrates a non-trivial example using realistic input data
    """

    def test_simple_election_is_valid(self) -> None:

        # Act
        subject = election_factory.get_hamilton_election_from_file()

        # Assert
        self.assertTrue(subject.is_valid())
