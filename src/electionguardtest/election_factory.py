from datetime import datetime
import os
from typing import TypeVar, Callable, Optional, Tuple, List

from hypothesis.strategies import (
    composite,
    emails,
    integers,
    text,
    SearchStrategy,
)

from electionguard.ballot import PlaintextBallot

from electionguard.election import (
    BallotStyle,
    CiphertextElectionContext,
    ElectionDescription,
    ElectionType,
    InternalElectionDescription,
    generate_placeholder_selections_from,
    GeopoliticalUnit,
    Candidate,
    Party,
    ContestDescription,
    SelectionDescription,
    ReportingUnitType,
    VoteVariationType,
    contest_description_with_placeholders_from,
    CandidateContestDescription,
    ReferendumContestDescription,
)

from electionguard.election_builder import ElectionBuilder

from electionguard.encrypt import contest_from

from electionguard.group import ElementModP
from electionguard.utils import get_optional

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]

here = os.path.abspath(os.path.dirname(__file__))


class ElectionFactory(object):

    simple_election_manifest_file_name = "election_manifest_simple.json"

    def get_simple_election_from_file(self) -> ElectionDescription:
        return self._get_election_from_file(self.simple_election_manifest_file_name)

    def get_fake_election(self) -> ElectionDescription:
        """
        Get a single Fake Election object that is manually constructed with default values
        """

        fake_ballot_style = BallotStyle("some-ballot-style-id")
        fake_ballot_style.geopolitical_unit_ids = ["some-geopoltical-unit-id"]

        fake_referendum_ballot_selections = [
            # Referendum selections are simply a special case of `candidate` in the object model
            SelectionDescription(
                "some-object-id-affirmative", "some-candidate-id-1", 0
            ),
            SelectionDescription("some-object-id-negative", "some-candidate-id-2", 1),
        ]

        sequence_order = 0
        number_elected = 1
        votes_allowed = 1
        fake_referendum_contest = ReferendumContestDescription(
            "some-referendum-contest-object-id",
            "some-geopoltical-unit-id",
            sequence_order,
            VoteVariationType.one_of_m,
            number_elected,
            votes_allowed,
            "some-referendum-contest-name",
            fake_referendum_ballot_selections,
        )

        fake_candidate_ballot_selections = [
            SelectionDescription(
                "some-object-id-candidate-1", "some-candidate-id-1", 0
            ),
            SelectionDescription(
                "some-object-id-candidate-2", "some-candidate-id-2", 1
            ),
            SelectionDescription(
                "some-object-id-candidate-3", "some-candidate-id-3", 2
            ),
        ]

        sequence_order_2 = 1
        number_elected_2 = 2
        votes_allowed_2 = 2
        fake_candidate_contest = CandidateContestDescription(
            "some-candidate-contest-object-id",
            "some-geopoltical-unit-id",
            sequence_order_2,
            VoteVariationType.one_of_m,
            number_elected_2,
            votes_allowed_2,
            "some-candidate-contest-name",
            fake_candidate_ballot_selections,
        )

        fake_election = ElectionDescription(
            election_scope_id="some-scope-id",
            type=ElectionType.unknown,
            start_date=datetime.now(),
            end_date=datetime.now(),
            geopolitical_units=[
                GeopoliticalUnit(
                    "some-geopoltical-unit-id",
                    "some-gp-unit-name",
                    ReportingUnitType.unknown,
                )
            ],
            parties=[Party("some-party-id-1"), Party("some-party-id-2")],
            candidates=[
                Candidate("some-candidate-id-1"),
                Candidate("some-candidate-id-2"),
                Candidate("some-candidate-id-3"),
            ],
            contests=[fake_referendum_contest, fake_candidate_contest],
            ballot_styles=[fake_ballot_style],
        )

        return fake_election

    def get_fake_ciphertext_election(
        self, description: ElectionDescription, elgamal_public_key: ElementModP
    ) -> Tuple[InternalElectionDescription, CiphertextElectionContext]:
        builder = ElectionBuilder(
            number_of_guardians=1, quorum=1, description=description
        )
        builder.set_public_key(elgamal_public_key)
        metadata, election = get_optional(builder.build())
        return metadata, election

    # TODO: Move to ballot Factory?
    def get_fake_ballot(
        self, election: ElectionDescription = None, ballot_id: str = None
    ) -> PlaintextBallot:
        """
        Get a single Fake Ballot object that is manually constructed with default vaules
        """
        if election is None:
            election = self.get_fake_election()

        if ballot_id is None:
            ballot_id = "some-unique-ballot-id-123"

        fake_ballot = PlaintextBallot(
            ballot_id,
            election.ballot_styles[0].object_id,
            [contest_from(election.contests[0]), contest_from(election.contests[1])],
        )

        return fake_ballot

    def _get_election_from_file(self, filename: str) -> ElectionDescription:
        with open(os.path.join(here, "data", filename), "r") as subject:
            data = subject.read()
            target = ElectionDescription.from_json(data)

        return target


@composite
def get_selection_description_well_formed(
    draw: _DrawType,
    ints=integers(1, 20),
    emails=emails(),
    candidate_id: Optional[str] = None,
    sequence_order: Optional[int] = None,
) -> Tuple[str, SelectionDescription]:
    if candidate_id is None:
        candidate_id = draw(emails)

    object_id = f"{candidate_id}-selection"

    if sequence_order is None:
        sequence_order = draw(ints)

    return (object_id, SelectionDescription(object_id, candidate_id, sequence_order))


@composite
def get_contest_description_well_formed(
    draw: _DrawType,
    ints=integers(1, 20),
    text=text(),
    emails=emails(),
    selections=get_selection_description_well_formed(),
    sequence_order: Optional[int] = None,
    electoral_district_id: Optional[str] = None,
) -> Tuple[str, ContestDescription]:
    object_id = f"{draw(emails)}-contest"

    if sequence_order is None:
        sequence_order = draw(ints)

    if electoral_district_id is None:
        electoral_district_id = f"{draw(emails)}-gp-unit"

    first_int = draw(ints)
    second_int = draw(ints)

    # TODO ISSUE #33: support more votes than seats for other VoteVariationType options
    number_elected = min(first_int, second_int)
    votes_allowed = number_elected

    selection_descriptions: List[SelectionDescription] = list()
    for i in range(max(first_int, second_int)):
        selection: Tuple[str, SelectionDescription] = draw(selections)
        _, selection_description = selection
        selection_description.sequence_order = i
        selection_descriptions.append(selection_description)

    contest_description = ContestDescription(
        object_id,
        electoral_district_id,
        sequence_order,
        VoteVariationType.n_of_m,
        number_elected,
        votes_allowed,
        draw(text),
        selection_descriptions,
    )

    placeholder_selections = generate_placeholder_selections_from(
        contest_description, number_elected
    )

    return (
        object_id,
        contest_description_with_placeholders_from(
            contest_description, placeholder_selections
        ),
    )
