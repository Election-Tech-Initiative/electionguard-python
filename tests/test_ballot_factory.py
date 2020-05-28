import unittest
from random import Random

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory
from electionguard.ballot import PlaintextBallotContest
from electionguard.election import (
    SelectionDescription,
    generate_placeholder_selections_from,
    contest_description_with_placeholders_from,
    ContestDescriptionWithPlaceholders,
    VoteVariationType,
)

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestBallotFactory(unittest.TestCase):
    @unittest.skip("doesn't work")
    def test_contest_simple1(self):
        # this tries to simplify and reproduce a failure that occurred in
        # test_decrypt_contest_valid_input_succeeds

        description = ContestDescriptionWithPlaceholders(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=0,
                ),
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=1,
                ),
            ],
            ballot_title=None,
            ballot_subtitle=None,
            placeholder_selections=[
                SelectionDescription(
                    object_id="0@A.com-contest-2-placeholder",
                    candidate_id="0@A.com-contest-2-candidate",
                    sequence_order=2,
                )
            ],
        )

        data: PlaintextBallotContest = ballot_factory.get_random_contest_from(
            description, Random(0)
        )

        self.assertTrue(
            data.is_valid(description.object_id, description.number_elected,)
        )

        placeholders = generate_placeholder_selections_from(description)
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )
