from random import Random
from typing import TypeVar, Callable, Tuple

from hypothesis.strategies import (
    composite,
    emails,
    booleans,
    integers,
    lists,
    SearchStrategy,
)

from electionguard.election import Candidate, ContestDescription
from electionguard.encrypt import (
    PlaintextBallotContest,
    PlaintextBallotSelection,
    PlaintextBallot,
    SelectionDescription,
    ContestDescriptionWithPlaceholders,
)

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def arb_candidate(draw: _DrawType, strs=emails(), bools=booleans()) -> Candidate:
    # We could use a more general definition of candidate names, including unicode, but arbitrary "email addresses"
    # are good enough to stress test things without generating unreadable test results.
    return Candidate(draw(strs), draw(bools), draw(bools), draw(bools))


@composite
def arb_contest_description(
    draw: _DrawType, strs=emails(), ints=integers(1, 6)
) -> ContestDescription:
    number_elected = draw(ints)
    votes_allowed = draw(ints)

    # we have to satisfy an invariant that number_elected <= votes_allowed
    if number_elected > votes_allowed:
        number_elected = votes_allowed

    ballot_selections = draw(
        lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed)
    )
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(
        draw(strs),
        ballot_selections,
        draw(strs),
        draw(strs),
        draw(strs),
        draw(strs),
        number_elected,
        votes_allowed,
    )


@composite
def arb_contest_description_room_for_overvoting(
    draw: _DrawType, strs=emails(), ints=integers(2, 6)
) -> ContestDescription:
    number_elected = draw(ints)
    votes_allowed = draw(ints)

    if number_elected >= votes_allowed:
        number_elected = votes_allowed - 1

    ballot_selections = draw(
        lists(arb_candidate(), min_size=votes_allowed, max_size=votes_allowed)
    )
    assert len(ballot_selections) == votes_allowed
    return ContestDescription(
        draw(strs),
        ballot_selections,
        draw(strs),
        draw(strs),
        draw(strs),
        draw(strs),
        number_elected,
        votes_allowed,
    )


def contest_description_to_plaintext_voted_contest(
    random_seed: int, cds: ContestDescription
) -> PlaintextVotedContest:
    """
    This is used by `arb_plaintext_voted_contest_well_formed` and other generators. Given a contest
    description and a random seed, produce a well-formed plaintext voted contest.
    """
    r = Random()
    r.seed(random_seed)

    # We're going to create a list of numbers, with the right number of 1's and 0's, then shuffle it based on the seed.
    # Note that we're not generating vote selections with undervotes, because those shouldn't exist at this stage in
    # ElectionGuard. If the voter chooses to undervote, the "dummy" votes should become one, and thus there's no such
    # thing as an undervoted ballot plaintext.

    selections = [1] * cds.number_elected + [0] * (
        cds.votes_allowed - cds.number_elected
    )

    assert len(selections) == cds.votes_allowed

    r.shuffle(selections)
    return PlaintextVotedContest(cds.crypto_hash(), selections)


@composite
def arb_plaintext_voted_contest_well_formed(
    draw: _DrawType, cds=arb_contest_description(), seed=integers()
) -> Tuple[ContestDescription, PlaintextVotedContest]:
    s = draw(seed)
    contest_description: ContestDescription = draw(cds)

    return (
        contest_description,
        contest_description_to_plaintext_voted_contest(s, contest_description),
    )


@composite
def arb_plaintext_voted_contest_overvote(
    draw: _DrawType,
    cds=arb_contest_description_room_for_overvoting(),
    seed=integers(),
    overvotes=integers(1, 6),
) -> Tuple[ContestDescription, PlaintextVotedContest]:
    r = Random()
    r.seed(draw(seed))
    contest_description: ContestDescription = draw(cds)
    overvote: int = draw(overvotes)

    assert contest_description.number_elected < contest_description.votes_allowed

    if (
        contest_description.number_elected + overvote
        > contest_description.votes_allowed
    ):
        overvote = (
            contest_description.votes_allowed - contest_description.number_elected
        )

    selections = [1] * (contest_description.number_elected + overvote) + [0] * (
        contest_description.votes_allowed
        - contest_description.number_elected
        - overvote
    )

    assert len(selections) == contest_description.votes_allowed

    r.shuffle(selections)
    return (
        contest_description,
        PlaintextVotedContest(contest_description.crypto_hash(), selections),
    )
