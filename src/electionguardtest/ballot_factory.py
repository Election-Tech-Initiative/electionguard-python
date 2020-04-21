from datetime import datetime
import os
from random import Random
from secrets import randbelow
from typing import TypeVar, Callable, Tuple

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
    PlaintextBallotSelection
)

from electionguard.election import (
    BallotStyle,
    CyphertextElection,
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

here = os.path.abspath(os.path.dirname(__file__))

class BallotFactory(object):
    simple_ballot_filename = 'ballot_in_simple.json'

    def get_simple_ballot_from_file(self) -> PlaintextBallot:
        return self._get_ballot_from_file(self.simple_ballot_filename)

    def _get_ballot_from_file(self, filename: str) -> PlaintextBallot:
        with open(os.path.join(here, 'data', filename), 'r') as subject:
            data = subject.read()
            target = PlaintextBallot.from_json(data)

        return target

@composite
def get_selection_well_formed(
    draw: _DrawType, uuids=uuids(), bools=booleans(), text=text()) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extra_data = None
    else:
        extra_data = draw(text)
    object_id = f"selection-{draw(uuids)}"
    return (object_id, PlaintextBallotSelection(object_id, f"{draw(bools)}", f"{draw(bools)}", extra_data))

@composite
def get_selection_poorly_formed(
    draw: _DrawType, uuids=uuids(), bools=booleans(), text=text()) -> Tuple[str, PlaintextBallotSelection]:
    use_none = draw(bools)
    if use_none:
        extra_data = None
    else:
        extra_data = draw(text)
    object_id = f"selection-{draw(uuids)}"
    return (object_id, PlaintextBallotSelection(object_id, f"{draw(text)}", f"{draw(bools)}", extra_data))

# @composite
# def get_contest_well_formed(
#     draw: _DrawType, uuids=uuids(), bools=booleans(), ints=integers(1,10), text=text(), selections=get_selection_well_formed()
#     ) -> Tuple[str, PlaintextBallotContest]:
#     pass

