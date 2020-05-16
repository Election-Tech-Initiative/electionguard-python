from random import Random
from typing import TypeVar, Callable, Tuple, List

from hypothesis.provisional import urls
from hypothesis.strategies import (
    composite,
    emails,
    booleans,
    integers,
    lists,
    SearchStrategy,
    text,
    uuids,
    datetimes,
)

from electionguard.election import (
    Candidate,
    ContestDescription,
    ElectionType,
    ReportingUnitType,
    VoteVariationType,
    ContactInformation,
    GeopoliticalUnit,
    BallotStyle,
    Language,
    InternationalizedText,
    AnnotatedString,
    Party,
)

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def arb_election_type(draw: _DrawType):
    n = draw(integers(0, 7))
    return ElectionType(n)


@composite
def arb_reporting_unit_type(draw: _DrawType):
    n = draw(integers(0, 28))
    return ReportingUnitType(n)


@composite
def arb_contact_information(draw: _DrawType):
    # empty lists for email and phone, for now
    return ContactInformation(draw(emails()), None, None, draw(emails()))


@composite
def arb_two_letter_code(
    draw: _DrawType,
    lang=text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=2, max_size=2),
):
    return draw(lang)


@composite
def arb_language(draw: _DrawType):
    return Language(draw(emails()), draw(arb_two_letter_code()))


@composite
def arb_internationalized_text(draw: _DrawType):
    return InternationalizedText(draw(lists(arb_language(), min_size=1, max_size=3)))


@composite
def arb_annotated_string(draw: _DrawType):
    s = draw(arb_language())
    # no idea what the annotations should be, so we'll just use two-letter language codes, because why not?
    return AnnotatedString(annotation=s.language, value=s.value)


@composite
def arb_ballot_style(draw: _DrawType, party_ids: List[Party]):
    gids = None
    pids = [x.get_party_id() for x in party_ids]
    if len(pids) == 0:
        pids = None
    image_uri = draw(urls())
    return BallotStyle(str(draw(uuids())), gids, pids, image_uri)


@composite
def arb_party_list(draw: _DrawType, num_parties: int):
    party_names = [f"Party{n}" for n in range(0, num_parties)]
    party_abbrvs = [f"P{n}" for n in range(0, num_parties)]

    return [
        Party(
            object_id=str(draw(uuids())),
            ballot_name=InternationalizedText([Language(party_names[i], "en")]),
            abbreviation=party_abbrvs[i],
            color=None,
            logo_uri=draw(urls()),
        )
        for i in range(0, num_parties)
    ]


@composite
def arb_geopolitical_unit(
    draw: _DrawType,
    id=uuids(),
    s=emails(),
    reporting=arb_reporting_unit_type(),
    contact=arb_contact_information(),
):
    return GeopoliticalUnit(str(draw(id)), draw(s), draw(reporting), draw(contact))


@composite
def arb_candidate(draw: _DrawType, pid: str):
    bools = booleans()
    return Candidate(
        str(draw(id)),
        draw(arb_internationalized_text()),
        draw(pid) if draw(bools) else None,
        draw(urls()) if draw(bools) else None,
    )


@composite
def arb_contest_description(draw: _DrawType, sequence_number: int):
    n = draw(integers(0, 3))
    m = n + draw(integers(0, 3))  # for an n-of-m election
    parties = draw(arb_party_list(m))
    party_ids = [p.abbreviation for p in parties]
