from tests.base_test_case import BaseTestCase

import electionguard_tools.factories.election_factory as ElectionFactory
import electionguard_tools.factories.ballot_factory as BallotFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestHamiltonCountyElection(BaseTestCase):
    """
    Demonstrates a non-trivial example using realistic input data
    """

    def test_manifest_is_valid(self) -> None:

        # Act
        subject = election_factory.get_hamilton_manifest_from_file()

        # Assert
        self.assertTrue(subject.is_valid())
