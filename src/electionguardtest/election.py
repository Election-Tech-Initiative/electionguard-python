from functools import reduce
from random import Random
from typing import TypeVar, Callable, List, Optional, Tuple

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

from electionguard.ballot import PlaintextBallotContest, PlaintextBallot
from electionguard.election import (
    Candidate,
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
    CandidateContestDescription,
    ReferendumContestDescription,
    DerivedContestType,
    ElectionDescription,
    InternalElectionDescription,
    CiphertextElection,
)
from electionguard.encrypt import selection_from
from electionguardtest.elgamal import arb_elgamal_keypair

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]

_first_names = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Barbara",
    "Richard",
    "Susan",
    "Joseph",
    "Jessica",
    "Thomas",
    "Sarah",
    "Charles",
    "Karen",
    "Christopher",
    "Nancy",
    "Daniel",
    "Margaret",
    "Matthew",
    "Lisa",
    "Anthony",
    "Betty",
    "Donald",
    "Dorothy",
]

_last_names = [
    "SMITH",
    "JOHNSON",
    "WILLIAMS",
    "JONES",
    "BROWN",
    "DAVIS",
    "MILLER",
    "WILSON",
    "MOORE",
    "TAYLOR",
    "ANDERSON",
    "THOMAS",
    "JACKSON",
    "WHITE",
    "HARRIS",
    "MARTIN",
    "THOMPSON",
    "GARCIA",
    "MARTINEZ",
    "ROBINSON",
    "CLARK",
    "RODRIGUEZ",
    "LEWIS",
    "LEE",
    "WALKER",
    "HALL",
    "ALLEN",
    "YOUNG",
    "HERNANDEZ",
    "KING",
    "WRIGHT",
    "LOPEZ",
    "HILL",
    "SCOTT",
    "GREEN",
    "ADAMS",
    "BAKER",
    "GONZALEZ",
]


@composite
def arb_human_name(draw: _DrawType):
    """
    Generates a string with a human first and last name (based on popular first and last names in the U.S.).
    """
    return f"{_first_names[draw(integers(0, len(_first_names) - 1))]} {_last_names[draw(integers(0, len(_last_names) - 1))]}"


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
    return ContactInformation(None, draw(emails()), None, draw(arb_human_name()))


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
def arb_language_human_name(draw: _DrawType):
    return Language(draw(arb_human_name()), draw(arb_two_letter_code()))


@composite
def arb_internationalized_text(draw: _DrawType):
    return InternationalizedText(draw(lists(arb_language(), min_size=1, max_size=3)))


@composite
def arb_internationalized_human_name(draw: _DrawType):
    return InternationalizedText(
        draw(lists(arb_language_human_name(), min_size=1, max_size=3))
    )


@composite
def arb_annotated_string(draw: _DrawType):
    s = draw(arb_language())
    # TODO: no idea what the annotations should be, so we'll just use two-letter language codes.
    #   What actually goes here?
    return AnnotatedString(annotation=s.language, value=s.value)


@composite
def arb_ballot_style(
    draw: _DrawType, party_ids: List[Party], geo_units: List[GeopoliticalUnit]
):
    assert len(party_ids) > 0
    assert len(geo_units) > 0

    gids = [geo_units[0].object_id]  # any reason to use others?
    pids = [x.get_party_id() for x in party_ids]
    if len(pids) == 0:
        pids = None
    image_uri = draw(urls())
    return BallotStyle(str(draw(uuids())), gids, pids, image_uri)


@composite
def arb_party_list(draw: _DrawType, num_parties: int):
    party_names = [f"Party{n}" for n in range(num_parties)]
    party_abbrvs = [f"P{n}" for n in range(num_parties)]

    assert num_parties > 0

    return [
        Party(
            object_id=str(draw(uuids())),
            ballot_name=InternationalizedText([Language(party_names[i], "en")]),
            abbreviation=party_abbrvs[i],
            color=None,
            logo_uri=draw(urls()),
        )
        for i in range(num_parties)
    ]


@composite
def arb_geopolitical_unit(draw: _DrawType):
    return GeopoliticalUnit(
        str(draw(uuids())),
        draw(emails()),
        draw(arb_reporting_unit_type()),
        draw(arb_contact_information()),
    )


@composite
def arb_candidate(draw: _DrawType, party_list: Optional[List[Party]]):
    """
    Generates a Candidate, assigning it one of the parties from `party_list` at random,
    with a chance that there will be no party assigned at all.
    :param draw: Hidden argument, used by Hypothesis.
    :param party_list: A list of `Party` objects. If None, then the resulting `Candidate`
        will have no party.
    """
    bools = booleans()
    if party_list:
        party = party_list[draw(integers(0, len(party_list) - 1))]
        pid = party.get_party_id()
    else:
        pid = None

    return Candidate(
        str(draw(uuids())),
        draw(arb_internationalized_human_name()),
        pid,
        draw(urls()) if draw(bools) else None,
    )


@composite
def arb_candidate_contest_description(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
    n: Optional[int] = None,
    m: Optional[int] = None,
):
    """
    Generates a tuple: a list of candidates and a corresponding `CandidateContestDescription`.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: When you're making a ballot, it's going to be a list of contests.
        This is where you put the sequence number, starting at zero.
    :param party_list: A list of `Party` objects; each candidate's party is drawn at random from this list.
        See `arb_candidate` for details on this assignment.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    :param n: optional integer, specifying a particular value for n in this n-of-m contest, otherwise
        it's varied by Hypothesis.
    :param m: optional integer, specifying a particular value for m in this n-of-m contest, otherwise
        it's varied by Hypothesis.
    """

    if n is None:
        n = draw(integers(1, 3))
    if m is None:
        m = n + draw(integers(0, 3))  # for an n-of-m election

    party_ids = [p.get_party_id() for p in party_list]

    candidates = draw(lists(arb_candidate(party_list), min_size=m, max_size=m))
    selection_descriptions = [
        candidates[i].to_selection_description(i) for i in range(m)
    ]

    # TODO: right now, we're supporting one-of-m and n-of-m; we need to support other types later.
    return (
        candidates,
        CandidateContestDescription(
            object_id=str(draw(uuids())),
            electoral_district_id=geo_units[
                draw(integers(0, len(geo_units) - 1))
            ].object_id,
            sequence_order=sequence_order,
            vote_variation=VoteVariationType.one_of_m
            if n == 1
            else VoteVariationType.n_of_m,
            number_elected=n,
            votes_allowed=n,  # TODO: should this be None or n?
            name=draw(emails()),
            ballot_selections=selection_descriptions,
            ballot_title=draw(arb_internationalized_text()),
            ballot_subtitle=draw(arb_internationalized_text()),
            primary_party_ids=party_ids,
        ),
    )


@composite
def arb_contest_description_room_for_overvoting(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
):
    """
    Similar to `arb_contest_description`, but guarantees that for the n-of-m contest that n < m,
    therefore it's possible to construct an "overvoted" plaintext, which should then fail subsequent tests.
    """
    n = draw(integers(1, 3))
    m = n + draw(integers(1, 3))
    return draw(
        arb_candidate_contest_description(
            sequence_order=sequence_order,
            party_list=party_list,
            geo_units=geo_units,
            n=n,
            m=m,
        )
    )


@composite
def arb_referendum_contest_description(
    draw: _DrawType, sequence_order: int, geo_units: List[GeopoliticalUnit]
):
    """
    Generates a tuple: a list of party-less candidates and a corresponding `ReferendumContestDescription`.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: When you're making a ballot, it's going to be a list of contests.
        This is where you put the sequence number, starting at zero.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    """
    n = draw(integers(1, 3))

    candidates = draw(lists(arb_candidate(None), min_size=n, max_size=n))
    selection_descriptions = [
        candidates[i].to_selection_description(i) for i in range(n)
    ]

    return (
        candidates,
        ReferendumContestDescription(
            object_id=str(draw(uuids())),
            electoral_district_id=geo_units[
                draw(integers(0, len(geo_units) - 1))
            ].object_id,
            sequence_order=sequence_order,
            vote_variation=VoteVariationType.one_of_m,
            number_elected=1,
            votes_allowed=1,  # TODO: should this be None or 1?
            name=draw(emails()),
            ballot_selections=selection_descriptions,
            ballot_title=draw(arb_internationalized_text()),
            ballot_subtitle=draw(arb_internationalized_text()),
        ),
    )


@composite
def arb_contest_description(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
):
    """
    Generates either the result of `arb_referendum_contest_description` or `arb_candidate_contest_description`.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: When you're making a ballot, it's going to be a list of contests.
        This is where you put the sequence number, starting at zero.
    :param party_list: A list of `Party` objects; each candidate's party is drawn at random from this list.
        See `arb_candidate` for details on this assignment.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    """
    if draw(booleans()):
        return draw(arb_referendum_contest_description(sequence_order, geo_units))
    else:
        return draw(
            arb_candidate_contest_description(sequence_order, party_list, geo_units)
        )


@composite
def arb_election_description(
    draw: _DrawType, max_num_parties: int = 3, max_num_contests: int = 3
):
    """
    Generates an ElectionDescription, the top-level structure.
    :param draw: Hidden argument, used by Hypothesis.
    :param max_num_parties: The largest number of parties that will be generated (default: 20)
    :param max_num_contests: The largest number of contests that will be generated (default: 4)
    """
    assert max_num_parties > 0
    assert max_num_contests > 0

    geo_units = [draw(arb_geopolitical_unit())]
    num_parties: int = draw(integers(1, max_num_contests))
    parties: List[Party] = draw(arb_party_list(num_parties))
    num_contests: int = draw(integers(1, 4))  # keep this small so tests run faster
    contest_tuples: List[Tuple[List[Candidate], DerivedContestType]] = [
        draw(arb_contest_description(i, parties, geo_units))
        for i in range(num_contests)
    ]
    # contest_tuples: List[Tuple[List[Candidate], DerivedContestType]] = []
    # for i in range(num_contests):
    #     contest_tuples.append(draw(arb_contest_description(i, parties)))
    assert len(contest_tuples) > 0

    # TODO: there may be duplicates in the candidate list. Do we care? If so, we'd have to make
    #   the type hashable, such that we could convert to a set. Good enough left alone for now.
    candidates = reduce(lambda a, b: a + b, [c[0] for c in contest_tuples])
    contests = [c[1] for c in contest_tuples]

    # TODO: ElectionDescription has a *list* of ballot styles. It's wildly unclear what that's supposed
    #   to mean. So, at least for now, we'll return a list of size one, where the ballot style includes
    #   all the parties in it. See additional to-do notes next to the class BallotStyle definition.
    ballot_styles = [draw(arb_ballot_style(parties, geo_units))]

    start_date = draw(datetimes())
    end_date = start_date  # maybe later on we'll do something smarter with the dates

    return ElectionDescription(
        election_scope_id=draw(arb_language()),
        type=ElectionType.general,  # good enough for now
        start_date=start_date,
        end_date=end_date,
        geopolitical_units=geo_units,
        parties=parties,
        candidates=candidates,
        contests=contests,
        ballot_styles=ballot_styles,
        name=draw(arb_internationalized_text()),
        contact_information=draw(arb_contact_information()),
    )


@composite
def arb_plaintext_voted_ballot(draw: _DrawType, ied: InternalElectionDescription):
    """
    Given an `InternalElectionDescription` object, generates an arbitrary `PlaintextBallot` with the
    choices made randomly.
    :param draw: Hidden argument, used by Hypothesis.
    :param description: Any `InternalElectionDescription`
    """

    num_ballot_styles = len(ied.ballot_styles)
    assert (
        num_ballot_styles > 0
    ), "we shouldn't ever have an election with no ballot styles"

    # pick a ballot style at random
    bs = ied.ballot_styles[draw(integers(0, num_ballot_styles - 1))]
    bs_id = bs.object_id

    contests = ied.get_contests_for(bs_id)
    assert (
        len(contests) > 0
    ), "we shouldn't ever have a ballot style with no contests in it"

    voted_contests: List[PlaintextBallotContest] = []
    for c in contests:
        assert c.is_valid(), "every contest needs to be valid"
        n = c.number_elected  # we need exactly this many 1's, and the rest 0's
        ballot_selections = c.ballot_selections
        assert len(ballot_selections) >= n

        # TODO: assert something about having the same number of non-placeholders and otherwise satisfying a n-of-m
        #  ballot. (Or, write this up as a separate property-based test. Kinda hard to tease these individual properties
        #  apart when the individual parts don't work without being part of an overarching ElectionDescription.)

        random = Random(draw(integers()))
        random.shuffle(ballot_selections)
        yes_votes = ballot_selections[
            : draw(integers(0, n))
        ]  # we'll vote as few as zero selections and as many as n

        # TODO: write a variant on this test where we overvote, make sure that it's rejected later.

        voted_selections = [
            selection_from(x, is_placeholder=False, is_affirmative=True)
            for x in yes_votes
        ]

        voted_contests.append(PlaintextBallotContest(c.object_id, voted_selections))

    return PlaintextBallot(str(draw(uuids())), bs_id, voted_contests)


@composite
def arb_ciphertext_election(draw: _DrawType, ed: ElectionDescription):
    """
    Generates a tuple of a CiphertextElection and the secret key associated with it -- the context you need to do
    any of the encryption/decryption operations. These ones have exactly one trustee.
    """
    secret_key, public_key = draw(arb_elgamal_keypair())
    return secret_key, CiphertextElection(1, 1, public_key, ed.crypto_hash())


# TODO: a more general version of this that makes ballots of multiple ballot styles, allowing for more complex tallying.
#   arb_election_description() already generates multiple ballot styles, so we're half-way there.
@composite
def arb_election_and_ballots(draw: _DrawType, num_ballots: int = 3):
    """
    Generates a tuple of: an `ElectionDescription`, a list of plaintext ballots, an ElGamal secret key,
    and a `CiphertextElection`. Every ballot will match the same ballot style.
    """
    assert num_ballots >= 0, "You're asking for a negative number of ballots?"
    ed = draw(arb_election_description())
    ied = InternalElectionDescription(ed)

    ballots = [draw(arb_plaintext_voted_ballot(ied)) for _ in range(num_ballots)]

    secret_key, ce = draw(arb_ciphertext_election(ed))

    return ied, ballots, secret_key, ce
