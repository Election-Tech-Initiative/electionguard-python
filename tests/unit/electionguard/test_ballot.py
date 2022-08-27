from tests.base_test_case import BaseTestCase

from electionguard.manifest import (
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
    VoteVariationType,
)
from electionguard.encrypt import contest_from
from electionguard.utils import NullVoteException, OverVoteException, UnderVoteException


NUMBER_ELECTED = 2


def get_sample_contest_description() -> ContestDescriptionWithPlaceholders:
    ballot_selections = [
        SelectionDescription("option-1-id", 1, "luke-skywalker-id"),
        SelectionDescription("option-2-id", 2, "darth-vader-id"),
        SelectionDescription("option-3-id", 3, "obi-wan-kenobi-id"),
    ]
    placeholder_selections = [
        SelectionDescription("placeholder-1-id", 4, "placeholder-id"),
        SelectionDescription("placeholder-2-id", 5, "placeholder-id"),
    ]
    description = ContestDescriptionWithPlaceholders(
        "favorite-character-id",
        1,
        "dagobah-id",
        VoteVariationType.n_of_m,
        NUMBER_ELECTED,
        None,
        "favorite-star-wars-character",
        ballot_selections,
        None,
        None,
        placeholder_selections,
    )
    return description


class TestBallot(BaseTestCase):
    """Ballot tests"""

    def test_contest_valid(self) -> None:
        # Arrange.
        contest_description = get_sample_contest_description()
        contest = contest_from(contest_description)

        # Add Votes
        for i in range(NUMBER_ELECTED):
            contest.ballot_selections[i].vote = 1

        # Act & Assert.
        try:
            contest.valid(contest_description)
        except (NullVoteException, OverVoteException, UnderVoteException):
            self.fail("No exceptions should be thrown.")

    def test_contest_valid_with_null_vote(self) -> None:
        # Arrange.
        contest_description = get_sample_contest_description()
        null_vote = contest_from(contest_description)

        # Act & Assert.
        with self.assertRaises(NullVoteException):
            null_vote.valid(contest_description)

    def test_contest_valid_with_under_vote(self) -> None:
        # Arrange.
        contest_description = get_sample_contest_description()
        under_vote = contest_from(contest_description)

        # Add Votes
        for i in range(NUMBER_ELECTED - 1):
            under_vote.ballot_selections[i].vote = 1

        # Act & Assert.
        with self.assertRaises(UnderVoteException):
            under_vote.valid(contest_description)

    def test_contest_valid_with_over_vote(self) -> None:
        # Arrange.
        contest_description = get_sample_contest_description()
        over_vote = contest_from(contest_description)

        # Add Votes
        for i in range(NUMBER_ELECTED + 1):
            over_vote.ballot_selections[i].vote = 1

        # Act & Assert.
        with self.assertRaises(OverVoteException):
            over_vote.valid(contest_description)
