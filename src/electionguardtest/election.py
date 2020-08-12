from functools import reduce
from random import Random
from typing import TypeVar, Callable, List, Optional, Tuple

from hypothesis.provisional import urls
from hypothesis.strategies import (
    composite,
    emails,
    integers,
    lists,
    SearchStrategy,
    text,
    uuids,
    datetimes,
    one_of,
    just,
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
    ElectionDescription,
    InternalElectionDescription,
    CiphertextElectionContext,
    SelectionDescription,
    ContestDescription,
    make_ciphertext_election_context,
)
from electionguard.encrypt import selection_from
from electionguard.group import ElementModQ
from electionguardtest.elgamal import elgamal_keypairs

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
    "Sylvia",
    "Viktor",
    "Camille",
    "Mirai",
    "Anant",
    "Rohan",
    "François",
    "Altuğ",
    "Sigurður",
    "Böðmóður",
    "Quang Dũng",
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
    "STEELE-LOY",
    "O'CONNOR",
    "ANAND",
    "PATEL",
    "GUPTA",
    "ĐẶNG",
]


@composite
def human_names(draw: _DrawType):
    """
    Generates a string with a human first and last name.
    :param draw: Hidden argument, used by Hypothesis.
    """
    return f"{_first_names[draw(integers(0, len(_first_names) - 1))]} {_last_names[draw(integers(0, len(_last_names) - 1))]}"


@composite
def election_types(draw: _DrawType):
    """
    Generates an `ElectionType`.
    :param draw: Hidden argument, used by Hypothesis.
    """
    n = draw(integers(0, 7))
    return ElectionType(n)


@composite
def reporting_unit_types(draw: _DrawType):
    """
    Generates a `ReportingUnitType` object.
    :param draw: Hidden argument, used by Hypothesis.
    """
    n = draw(integers(0, 28))
    return ReportingUnitType(n)


@composite
def contact_infos(draw: _DrawType):
    """
    Generates a `ContactInformation` object.
    :param draw: Hidden argument, used by Hypothesis.
    """
    # empty lists for email and phone, for now
    return ContactInformation(None, draw(emails()), None, draw(human_names()))


@composite
def two_letter_codes(draw: _DrawType, min_size=2, max_size=2):
    """
    Generates a string with only a few characters, by default 2 letters
    from `a` to `z`, but configurable with the `min_size` and `max_size`
    parameters. Useful when you want something like a two-letter country
    or language code.
    :param draw: Hidden argument, used by Hypothesis.
    :param min_size: minimum number of characters to generate (default: 2)
    :param max_size: maximum number of characters to generate (default: 2)
    """
    return draw(
        text(
            alphabet="abcdefghijklmnopqrstuvwxyz", min_size=min_size, max_size=max_size
        )
    )


@composite
def languages(draw: _DrawType):
    """
    Generates a `Language` object with an arbitrary two-letter string as the code and
    something messier for the text ostensibly written in that language.
    :param draw: Hidden argument, used by Hypothesis.
    """
    return Language(draw(emails()), draw(two_letter_codes()))


@composite
def language_human_names(draw: _DrawType):
    """
    Generates a `Language` object with an arbitrary two-letter string as the code and
    a human name for the text ostensibly written in that language.
    :param draw: Hidden argument, used by Hypothesis.
    """
    return Language(draw(human_names()), draw(two_letter_codes()))


@composite
def internationalized_texts(draw: _DrawType):
    """
    Generates an `InternationalizedText` object with a list of `Language` objects
    within (representing a multilingual string).
    :param draw: Hidden argument, used by Hypothesis.
    """
    return InternationalizedText(draw(lists(languages(), min_size=1, max_size=3)))


@composite
def internationalized_human_names(draw: _DrawType):
    """
    Generates an `InternationalizedText` object with a list of `Language` objects
    within (representing a multilingual human name).
    :param draw: Hidden argument, used by Hypothesis.
    """
    return InternationalizedText(
        draw(lists(language_human_names(), min_size=1, max_size=3))
    )


@composite
def annotated_strings(draw: _DrawType):
    """
    Generates an `AnnotatedString` object with one `Language` and an associated
    `value` string.
    :param draw: Hidden argument, used by Hypothesis.
    """
    s = draw(languages())
    # We're just reusing the "value" string already associated with the language for now.
    return AnnotatedString(annotation=s.language, value=s.value)


@composite
def ballot_styles(
    draw: _DrawType, party_ids: List[Party], geo_units: List[GeopoliticalUnit]
):
    """
    Generates a `BallotStyle` object, which rolls up a list of parties and
    geopolitical units (passed as arguments), with some additional information
    added on as well.
    :param draw: Hidden argument, used by Hypothesis.
    :param party_ids: a list of `Party` objects to be used in this ballot style
    :param geo_units: a list of `GeopoliticalUnit` objects to be used in this ballot style
    """
    assert len(party_ids) > 0
    assert len(geo_units) > 0

    gp_unit_ids = [x.object_id for x in geo_units]
    if len(gp_unit_ids) == 0:
        gp_unit_ids = None

    party_ids = [x.get_party_id() for x in party_ids]
    if len(party_ids) == 0:
        party_ids = None

    image_uri = draw(urls())
    return BallotStyle(str(draw(uuids())), gp_unit_ids, party_ids, image_uri)


@composite
def party_lists(draw: _DrawType, num_parties: int):
    """
    Generates a `List[Party]` of the requested length.
    :param draw: Hidden argument, used by Hypothesis.
    :param num_parties: Number of parties to generate in the list.
    """
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
def geopolitical_units(draw: _DrawType):
    """
    Generates a `GeopoliticalUnit` object.
    :param draw: Hidden argument, used by Hypothesis.
    """
    return GeopoliticalUnit(
        object_id=str(draw(uuids())),
        name=draw(emails()),
        type=draw(reporting_unit_types()),
        contact_information=draw(contact_infos()),
    )


@composite
def candidates(draw: _DrawType, party_list: Optional[List[Party]]):
    """
    Generates a `Candidate` object, assigning it one of the parties from `party_list` at random,
    with a chance that there will be no party assigned at all.
    :param draw: Hidden argument, used by Hypothesis.
    :param party_list: A list of `Party` objects. If None, then the resulting `Candidate`
        will have no party.
    """
    if party_list:
        party = party_list[draw(integers(0, len(party_list) - 1))]
        party_id = party.get_party_id()
    else:
        party_id = None

    return Candidate(
        str(draw(uuids())),
        draw(internationalized_human_names()),
        party_id,
        draw(one_of(just(None), urls())),
    )


def _candidate_to_selection_description(
    candidate: Candidate, sequence_order: int
) -> SelectionDescription:
    """
    Given a `Candidate` and its position in a list of candidates, returns an equivalent
    `SelectionDescription`. The selection's `object_id` will contain the candidates's
    `object_id` within, but will have a "c-" prefix attached, so you'll be able to
    tell that they're related.
    """
    return SelectionDescription(
        f"c-{candidate.object_id}", candidate.get_candidate_id(), sequence_order
    )


@composite
def candidate_contest_descriptions(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
    n: Optional[int] = None,
    m: Optional[int] = None,
):
    """
    Generates a tuple: a `List[Candidate]` and a corresponding `CandidateContestDescription` for
    an n-of-m contest.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: integer describing the order of this contest; make these sequential when
        generating many contests.
    :param party_list: A list of `Party` objects; each candidate's party is drawn at random from this list.
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

    contest_candidates = draw(lists(candidates(party_list), min_size=m, max_size=m))
    selection_descriptions = [
        _candidate_to_selection_description(contest_candidates[i], i) for i in range(m)
    ]

    vote_variation = VoteVariationType.one_of_m if n == 1 else VoteVariationType.n_of_m

    return (
        contest_candidates,
        CandidateContestDescription(
            object_id=str(draw(uuids())),
            electoral_district_id=geo_units[
                draw(integers(0, len(geo_units) - 1))
            ].object_id,
            sequence_order=sequence_order,
            vote_variation=vote_variation,
            number_elected=n,
            votes_allowed=n,  # should this be None or n?
            name=draw(emails()),
            ballot_selections=selection_descriptions,
            ballot_title=draw(internationalized_texts()),
            ballot_subtitle=draw(internationalized_texts()),
            primary_party_ids=party_ids,
        ),
    )


@composite
def contest_descriptions_room_for_overvoting(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
):
    """
    Similar to `contest_descriptions`, but guarantees that for the n-of-m contest that n < m,
    therefore it's possible to construct an "overvoted" plaintext, which should then fail subsequent tests.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: integer describing the order of this contest; make these sequential when
        generating many contests.
    :param party_list: A list of `Party` objects; each candidate's party is drawn at random from this list.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    """
    n = draw(integers(1, 3))
    m = n + draw(integers(1, 3))
    return draw(
        candidate_contest_descriptions(
            sequence_order=sequence_order,
            party_list=party_list,
            geo_units=geo_units,
            n=n,
            m=m,
        )
    )


@composite
def referendum_contest_descriptions(
    draw: _DrawType, sequence_order: int, geo_units: List[GeopoliticalUnit]
):
    """
    Generates a tuple: a list of party-less candidates and a corresponding `ReferendumContestDescription`.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: integer describing the order of this contest; make these sequential when
        generating many contests.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    """
    n = draw(integers(1, 3))

    contest_candidates = draw(lists(candidates(None), min_size=n, max_size=n))
    selection_descriptions = [
        _candidate_to_selection_description(contest_candidates[i], i) for i in range(n)
    ]

    return (
        contest_candidates,
        ReferendumContestDescription(
            object_id=str(draw(uuids())),
            electoral_district_id=geo_units[
                draw(integers(0, len(geo_units) - 1))
            ].object_id,
            sequence_order=sequence_order,
            vote_variation=VoteVariationType.one_of_m,
            number_elected=1,
            votes_allowed=1,  # should this be None or 1?
            name=draw(emails()),
            ballot_selections=selection_descriptions,
            ballot_title=draw(internationalized_texts()),
            ballot_subtitle=draw(internationalized_texts()),
        ),
    )


@composite
def contest_descriptions(
    draw: _DrawType,
    sequence_order: int,
    party_list: List[Party],
    geo_units: List[GeopoliticalUnit],
):
    """
    Generates either the result of `referendum_contest_descriptions` or `candidate_contest_descriptions`.
    :param draw: Hidden argument, used by Hypothesis.
    :param sequence_order: integer describing the order of this contest; make these sequential when
        generating many contests.
    :param party_list: A list of `Party` objects; each candidate's party is drawn at random from this list.
        See `candidates` for details on this assignment.
    :param geo_units: A list of `GeopoliticalUnit`; one of these goes into the `electoral_district_id`
    """
    return draw(
        one_of(
            referendum_contest_descriptions(sequence_order, geo_units),
            candidate_contest_descriptions(sequence_order, party_list, geo_units),
        )
    )


@composite
def election_descriptions(
    draw: _DrawType, max_num_parties: int = 3, max_num_contests: int = 3
):
    """
    Generates an `ElectionDescription` -- the top-level object describing an election.
    :param draw: Hidden argument, used by Hypothesis.
    :param max_num_parties: The largest number of parties that will be generated (default: 3)
    :param max_num_contests: The largest number of contests that will be generated (default: 3)
    """
    assert max_num_parties > 0, "need at least one party"
    assert max_num_contests > 0, "need at least one contest"

    geo_units = [draw(geopolitical_units())]
    num_parties: int = draw(integers(1, max_num_parties))

    # keep this small so tests run faster
    parties: List[Party] = draw(party_lists(num_parties))
    num_contests: int = draw(integers(1, max_num_contests))

    # generate a collection candidates mapped to contest descritpions
    candidate_contests: List[Tuple[List[Candidate], ContestDescription]] = [
        draw(contest_descriptions(i, parties, geo_units)) for i in range(num_contests)
    ]
    assert len(candidate_contests) > 0

    candidates_ = reduce(
        lambda a, b: a + b,
        [candidate_contest[0] for candidate_contest in candidate_contests],
    )
    contests = [candidate_contest[1] for candidate_contest in candidate_contests]

    styles = [draw(ballot_styles(parties, geo_units))]

    # maybe later on we'll do something more complicated with dates
    start_date = draw(datetimes())
    end_date = start_date

    return ElectionDescription(
        election_scope_id=draw(emails()),
        type=ElectionType.general,  # good enough for now
        start_date=start_date,
        end_date=end_date,
        geopolitical_units=geo_units,
        parties=parties,
        candidates=candidates_,
        contests=contests,
        ballot_styles=styles,
        name=draw(internationalized_texts()),
        contact_information=draw(contact_infos()),
    )


@composite
def plaintext_voted_ballots(
    draw: _DrawType, metadata: InternalElectionDescription, count: int = 1
):
    """
    Given
    """
    if count == 1:
        return draw(plaintext_voted_ballot(metadata))
    ballots: List[PlaintextBallot] = []
    for i in range(count):
        ballots.append(draw(plaintext_voted_ballot(metadata)))
    return ballots


@composite
def plaintext_voted_ballot(draw: _DrawType, metadata: InternalElectionDescription):
    """
    Given an `InternalElectionDescription` object, generates an arbitrary `PlaintextBallot` with the
    choices made randomly.
    :param draw: Hidden argument, used by Hypothesis.
    :param metadata: Any `InternalElectionDescription`
    """

    num_ballot_styles = len(metadata.ballot_styles)
    assert num_ballot_styles > 0, "invalid election with no ballot styles"

    # pick a ballot style at random
    ballot_style = metadata.ballot_styles[draw(integers(0, num_ballot_styles - 1))]

    contests = metadata.get_contests_for(ballot_style.object_id)
    assert len(contests) > 0, "invalid ballot style with no contests in it"

    voted_contests: List[PlaintextBallotContest] = []
    for contest in contests:
        assert contest.is_valid(), "every contest needs to be valid"
        n = contest.number_elected  # we need exactly this many 1's, and the rest 0's
        ballot_selections = contest.ballot_selections
        assert len(ballot_selections) >= n

        random = Random(draw(integers()))
        random.shuffle(ballot_selections)
        cut_point = draw(integers(0, n))
        yes_votes = ballot_selections[:cut_point]
        no_votes = ballot_selections[cut_point:]

        voted_selections = [
            selection_from(description, is_placeholder=False, is_affirmative=True)
            for description in yes_votes
        ] + [
            selection_from(description, is_placeholder=False, is_affirmative=False)
            for description in no_votes
        ]

        voted_contests.append(
            PlaintextBallotContest(contest.object_id, voted_selections)
        )

    return PlaintextBallot(str(draw(uuids())), ballot_style.object_id, voted_contests)


CIPHERTEXT_ELECTIONS_TUPLE_TYPE = Tuple[ElementModQ, CiphertextElectionContext]


@composite
def ciphertext_elections(draw: _DrawType, election_description: ElectionDescription):
    """
    Generates a `CiphertextElectionContext` with a single public-private key pair as the encryption context.

    In a real election, the key ceremony would be used to generate a shared public key.

    :param draw: Hidden argument, used by Hypothesis.
    :param election_description: An `ElectionDescription` object, with which the `CiphertextElectionContext` will be associated
    :return: a tuple of a `CiphertextElectionContext` and the secret key associated with it
    """
    secret_key, public_key = draw(elgamal_keypairs())
    ciphertext_election_with_secret: CIPHERTEXT_ELECTIONS_TUPLE_TYPE = (
        secret_key,
        make_ciphertext_election_context(
            number_of_guardians=1,
            quorum=1,
            elgamal_public_key=public_key,
            description_hash=election_description.crypto_hash(),
        ),
    )
    return ciphertext_election_with_secret


ELECTIONS_AND_BALLOTS_TUPLE_TYPE = Tuple[
    ElectionDescription,
    InternalElectionDescription,
    List[PlaintextBallot],
    ElementModQ,
    CiphertextElectionContext,
]


@composite
def elections_and_ballots(draw: _DrawType, num_ballots: int = 3):
    """
    A convenience generator to generate all of the necessary components for simulating an election.
    Every ballot will match the same ballot style. Hypothesis doesn't
    let us declare a type hint on strategy return values, so you can use `ELECTIONS_AND_BALLOTS_TUPLE_TYPE`.

    :param draw: Hidden argument, used by Hypothesis.
    :param num_ballots: The number of ballots to generate (default: 3).
    :reeturn: a tuple of: an `InternalElectionDescription`, a list of plaintext ballots, an ElGamal secret key,
        and a `CiphertextElectionContext`
    """
    assert num_ballots >= 0, "You're asking for a negative number of ballots?"
    election_description = draw(election_descriptions())
    internal_election_description = InternalElectionDescription(election_description)

    ballots = [
        draw(plaintext_voted_ballots(internal_election_description))
        for _ in range(num_ballots)
    ]

    secret_key, context = draw(ciphertext_elections(election_description))

    mock_election: ELECTIONS_AND_BALLOTS_TUPLE_TYPE = (
        election_description,
        internal_election_description,
        ballots,
        secret_key,
        context,
    )
    return mock_election
