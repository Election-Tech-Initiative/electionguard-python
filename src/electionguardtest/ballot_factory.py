import os
from random import Random
from typing import TypeVar, Callable, List, Tuple, Optional

from hypothesis.strategies import (
    composite,
    emails,
    booleans,
    integers,
    lists,
    text,
    uuids,
    SearchStrategy,
)

from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)

from electionguard.election import ContestDescription, SelectionDescription

from electionguard.encrypt import selection_from

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]

here = os.path.abspath(os.path.dirname(__file__))


class BallotFactory(object):
    simple_ballot_filename = "ballot_in_simple.json"

    def get_random_selection_from(
        self,
        description: SelectionDescription,
        random_source: Random,
        is_placeholder=False,
    ) -> PlaintextBallotSelection:
        selected = (
            bool(random_source.randint(0, 1))
            if random_source is not None
            else bool(random_source.randint(0, 1))
        )
        return selection_from(description, is_placeholder, selected)

    def get_random_contest_from(
        self, description: ContestDescription, random: Random
    ) -> PlaintextBallotContest:
        """
        Get a randomly filled contest for the given description that 
        may be undervoted and may include explicitly false votes.
        For testing purposes, the optional field "random_seed" may
        be provided to make this function deterministic.
        """
        selections: List[PlaintextBallotSelection] = list()

        voted = 0

        for selection_description in description.ballot_selections:
            selection = self.get_random_selection_from(selection_description, random)
            voted += selection.to_int()
            # Possibly append the true selection, indicating an undervote
            if voted <= description.number_elected and bool(random.randint(0, 1)) == 1:
                selections.append(selection)
            # Possibly append the false selections as well, indicating some choices
            # may be explicitly false
            elif bool(random.randint(0, 1)) == 1:
                selections.append(selection_from(selection_description))

        return PlaintextBallotContest(description.object_id, selections)

    def get_simple_ballot_from_file(self) -> PlaintextBallot:
        return self._get_ballot_from_file(self.simple_ballot_filename)

    def _get_ballot_from_file(self, filename: str) -> PlaintextBallot:
        with open(os.path.join(here, "data", filename), "r") as subject:
            data = subject.read()
            target = PlaintextBallot.from_json(data)
        return target


@composite
def get_selection_well_formed(
    draw: _DrawType, uuids=uuids(), bools=booleans(), text=text()
) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extra_data = None
    else:
        extra_data = draw(text)
    object_id = f"selection-{draw(uuids)}"
    return (
        object_id,
        PlaintextBallotSelection(object_id, f"{draw(bools)}", draw(bools), extra_data),
    )


@composite
def get_selection_poorly_formed(
    draw: _DrawType, uuids=uuids(), bools=booleans(), text=text()
) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extra_data = None
    else:
        extra_data = draw(text)
    object_id = f"selection-{draw(uuids)}"
    return (
        object_id,
        PlaintextBallotSelection(object_id, f"{draw(text)}", draw(bools), extra_data),
    )
