from datetime import datetime
from random import Random
from secrets import randbelow
from typing import TypeVar, Callable, Tuple

from hypothesis.strategies import (
    composite,
    emails,
    booleans,
    integers,
    lists,
    SearchStrategy,
)

from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection
)

from electionguard.election import (
    BallotStyle,
    Election,
    ElectionType,
    GeopoliticalUnit,
    Candidate,
    Party,
    ContestDescription,
    SelectionDescription,
    ReportingUnitType,
    VoteVariationType
)

from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
)

from electionguard.encryption_compositor import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from
)

from electionguard.group import (
    ElementModQ,
    ONE_MOD_Q,
    int_to_q,
    add_q,
    unwrap_optional,
    Q,
    TWO_MOD_P,
    mult_p,
)

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]

class ElectionFactory(object):

    def get_fake_election(self) -> Election:
        """
        Get a single Fake Election object that is manually constructed with default values
        """

        fake_ballot_style = BallotStyle("some-ballot-style-id")
        fake_ballot_style.geopolitical_unit_ids = [
            "some-geopoltical-unit-id"
        ]

        fake_referendum_contest = ContestDescription(
            "some-referendum-contest-object-id", "some-geopoltical-unit-id", 0, VoteVariationType.one_of_m, 1, 1)
        fake_referendum_contest.ballot_selections = [
            # Referendum selections are simply a special case of `candidate` in the object model
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-1", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-2", 1),
        ]
        fake_referendum_contest.votes_allowed = 1

        fake_candidate_contest = ContestDescription(
            "some-candidate-contest-object-id", "some-geopoltical-unit-id", 1, VoteVariationType.one_of_m, 2, 2)
        fake_candidate_contest.ballot_selections = [
            SelectionDescription("some-object-id-candidate-1", "some-candidate-id-1", 0),
            SelectionDescription("some-object-id-candidate-2", "some-candidate-id-2", 1),
            SelectionDescription("some-object-id-candidate-3", "some-candidate-id-3", 2)
        ]
        fake_candidate_contest.votes_allowed = 2

        fake_election = Election(
            election_scope_id = "some-scope-id",
            type = ElectionType.unknown,
            start_date = datetime.now(),
            end_date = datetime.now(),
            geopolitical_units = [
                GeopoliticalUnit("some-geopoltical-unit-id", "some-gp-unit-name", ReportingUnitType.unknown)
            ],
            parties = [
                Party("some-party-id-1"),
                Party("some-party-id-2")
            ],
            candidates = [
                Candidate("some-candidate-id-1"),
                Candidate("some-candidate-id-2"),
                Candidate("some-candidate-id-3"),
            ],
            contests = [
                fake_referendum_contest,
                fake_candidate_contest
            ],
            ballot_styles = [
                fake_ballot_style
            ]
        )

        return fake_election

    def get_fake_ballot(self, election: Election = None) -> PlaintextBallot:
        """
        Get a single Fake Ballot object that is manually constructed with default vaules
        """
        if election is None:
            election = self.get_fake_election()
        
        fake_ballot = PlaintextBallot(
            "some-unique-ballot-id-123", 
            election.ballot_styles[0].object_id, 
            [
                contest_from(election.contests[0]),
                contest_from(election.contests[1])
            ])

        return fake_ballot

    #def generate_candidate(draw: _DrawType, strs=emails(), bools=booleans()) -> Candidate:

    