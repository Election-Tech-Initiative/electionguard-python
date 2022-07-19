from typing import Any, TypeVar, Callable, List, Tuple, Optional
import os
from random import Random, randint
import uuid

from hypothesis.strategies import (
    composite,
    booleans,
    integers,
    text,
    uuids,
    SearchStrategy,
)

from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)
from electionguard.encrypt import selection_from
from electionguard.manifest import (
    ContestDescription,
    SelectionDescription,
    InternalManifest,
)
from electionguard.serialize import from_file, from_list_in_file


_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]

_data = os.path.realpath(os.path.join(__file__, "../../../../data"))


class BallotFactory:
    """Factory to create ballots"""

    simple_ballot_filename = "ballot_in_simple.json"
    simple_ballots_filename = "plaintext_ballots_simple.json"

    @staticmethod
    def get_random_selection_from(
        description: SelectionDescription,
        random_source: Random,
        is_placeholder: bool = False,
    ) -> PlaintextBallotSelection:

        selected = bool(random_source.randint(0, 1))
        return selection_from(description, is_placeholder, selected)

    @staticmethod
    def get_random_contest_from(
        description: ContestDescription,
        random: Random,
        suppress_validity_check: bool = False,
        allow_null_votes: bool = True,
        allow_under_votes: bool = True,
    ) -> PlaintextBallotContest:
        """
        Get a randomly filled contest for the given description that
        may be undervoted and may include explicitly false votes.
        Since this is only used for testing, the random number generator
        (`random`) must be provided to make this function deterministic.
        """
        if not suppress_validity_check:
            assert description.is_valid(), "the contest description must be valid"

        shuffled_selections = description.ballot_selections[:]
        random.shuffle(shuffled_selections)

        if allow_null_votes and not allow_under_votes:
            cut_point = random.choice([0, description.number_elected])
        else:
            min_votes = description.number_elected
            if allow_under_votes:
                min_votes = 1
            if allow_null_votes:
                min_votes = 0
            cut_point = random.randint(min_votes, description.number_elected)

        selections = [
            selection_from(selection_description, is_affirmative=True)
            for selection_description in shuffled_selections[0:cut_point]
        ]

        for selection_description in shuffled_selections[cut_point:]:
            # Possibly append the false selections as well, indicating some choices
            # may be explicitly false
            if bool(random.randint(0, 1)) == 1:
                selections.append(
                    selection_from(selection_description, is_affirmative=False)
                )

        random.shuffle(selections)
        return PlaintextBallotContest(description.object_id, selections)

    def get_fake_ballot(
        self,
        internal_manifest: InternalManifest,
        ballot_id: str = None,
        allow_null_votes: bool = False,
    ) -> PlaintextBallot:
        """
        Get a single Fake Ballot object that is manually constructed with default vaules
        """

        if ballot_id is None:
            ballot_id = "some-unique-ballot-id-123"

        contests: List[PlaintextBallotContest] = []
        for contest in internal_manifest.get_contests_for(
            internal_manifest.ballot_styles[0].object_id
        ):
            contests.append(
                self.get_random_contest_from(
                    contest, Random(), allow_null_votes=allow_null_votes
                )
            )

        fake_ballot = PlaintextBallot(
            ballot_id, internal_manifest.ballot_styles[0].object_id, contests
        )

        return fake_ballot

    def generate_fake_plaintext_ballots_for_election(
        self,
        internal_manifest: InternalManifest,
        number_of_ballots: int,
        ballot_style_id: Optional[str] = None,
        allow_null_votes: bool = False,
        allow_under_votes: bool = True,
    ) -> List[PlaintextBallot]:
        ballots: List[PlaintextBallot] = []
        for _i in range(number_of_ballots):
            if ballot_style_id is not None:
                ballot_style = internal_manifest.get_ballot_style(ballot_style_id)
            else:
                style_index = randint(0, len(internal_manifest.ballot_styles) - 1)
                ballot_style = internal_manifest.ballot_styles[style_index]

            ballot_id = f"ballot-{uuid.uuid1()}"

            contests: List[PlaintextBallotContest] = []
            for contest in internal_manifest.get_contests_for(ballot_style.object_id):
                contests.append(
                    self.get_random_contest_from(
                        contest,
                        Random(),
                        allow_null_votes=allow_null_votes,
                        allow_under_votes=allow_under_votes,
                    )
                )

            ballots.append(PlaintextBallot(ballot_id, ballot_style.object_id, contests))

        return ballots

    def get_simple_ballot_from_file(self) -> PlaintextBallot:
        return self._get_ballot_from_file(self.simple_ballot_filename)

    def get_simple_ballots_from_file(self) -> List[PlaintextBallot]:
        return self._get_ballots_from_file(self.simple_ballots_filename)

    @staticmethod
    def _get_ballot_from_file(filename: str) -> PlaintextBallot:
        return from_file(PlaintextBallot, os.path.join(_data, filename))

    @staticmethod
    def _get_ballots_from_file(filename: str) -> List[PlaintextBallot]:
        return from_list_in_file(PlaintextBallot, os.path.join(_data, filename))


# TODO Migrate to strategies
@composite
def get_selection_well_formed(
    draw: _DrawType,
    ids: Any = uuids(),
    bools: Any = booleans(),
    txt: Any = text(),
    vote: Any = integers(0, 1),
) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extended_data = None
    else:
        extended_data = draw(txt)
    object_id = f"selection-{draw(ids)}"
    return (
        object_id,
        PlaintextBallotSelection(object_id, draw(vote), draw(bools), extended_data),
    )


# TODO Migrate to strategies
@composite
def get_selection_poorly_formed(
    draw: _DrawType,
    ids: Any = uuids(),
    bools: Any = booleans(),
    txt: Any = text(),
    vote: Any = integers(0, 1),
) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extended_data = None
    else:
        extended_data = draw(txt)
    object_id = f"selection-{draw(ids)}"
    return (
        object_id,
        PlaintextBallotSelection(object_id, draw(vote), draw(bools), extended_data),
    )
