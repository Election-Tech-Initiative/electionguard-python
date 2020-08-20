from dataclasses import dataclass, field, InitVar
from datetime import datetime
from enum import Enum, unique
from typing import cast, List, Optional, Set, Any

from .ballot import _list_eq
from .election_object_base import ElectionObjectBase
from .group import Q, P, R, G, ElementModQ, ElementModP
from .hash import CryptoHashable, hash_elems
from .logs import log_warning
from .serializable import Serializable
from .utils import get_optional


@unique
class ElectionType(Enum):
    """
    enumerations for the `ElectionReport` entity
    see: https://developers.google.com/elections-data/reference/election-type
    """

    unknown = 0
    general = 1
    partisan_primary_closed = 2
    partisan_primary_open = 3
    primary = 4
    runoff = 5
    special = 6
    other = 7


@unique
class ReportingUnitType(Enum):
    """
    Enumeration for the type of geopolitical unit
    see: https://developers.google.com/elections-data/reference/reporting-unit-type
    """

    unknown = 0
    ballot_batch = 1
    ballot_style_area = 2
    borough = 3
    city = 4
    city_council = 5
    combined_precinct = 6
    congressional = 7
    country = 8
    county = 9
    county_council = 10
    drop_box = 11
    judicial = 12
    municipality = 13
    polling_place = 14
    precinct = 15
    school = 16
    special = 17
    split_precinct = 18
    state = 19
    state_house = 20
    state_senate = 21
    township = 22
    utility = 23
    village = 24
    vote_center = 25
    ward = 26
    water = 27
    other = 28


@unique
class VoteVariationType(Enum):
    """
    Enumeration for contest algorithm or rules in the `Contest` entity
    see: https://developers.google.com/elections-data/reference/vote-variation
    """

    unknown = 0
    one_of_m = 1
    approval = 2
    borda = 3
    cumulative = 4
    majority = 5
    n_of_m = 6
    plurality = 7
    proportional = 8
    range = 9
    rcv = 10
    super_majority = 11
    other = 12


@dataclass(eq=True, unsafe_hash=True)
class AnnotatedString(Serializable, CryptoHashable):
    """
    Use this as a type for character strings.
    See: https://developers.google.com/elections-data/reference/annotated-string
    """

    annotation: str = field(default="")
    value: str = field(default="")

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(self.annotation, self.value)


@dataclass(eq=True, unsafe_hash=True)
class Language(Serializable, CryptoHashable):
    """
    The ISO-639 language
    see: https://en.wikipedia.org/wiki/ISO_639
    """

    value: str
    language: str = field(default="en")

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(self.value, self.language)


@dataclass(eq=True, unsafe_hash=True)
class InternationalizedText(Serializable, CryptoHashable):
    """
    Data entity used to represent multi-national text. Use when text on a ballot contains multi-national text.
    See: https://developers.google.com/elections-data/reference/internationalized-text
    """

    text: List[Language] = field(default_factory=lambda: [])

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(self.text)


@dataclass(eq=True, unsafe_hash=True)
class ContactInformation(Serializable, CryptoHashable):
    """
    For defining contact information about objects such as persons, boards of authorities, and organizations.
    See: https://developers.google.com/elections-data/reference/contact-information
    """

    address_line: Optional[List[str]] = field(default=None)
    email: Optional[List[AnnotatedString]] = field(default=None)
    phone: Optional[List[AnnotatedString]] = field(default=None)
    name: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(self.name, self.address_line, self.email, self.phone)


@dataclass(eq=True, unsafe_hash=True)
class GeopoliticalUnit(ElectionObjectBase, CryptoHashable):
    """
    Use this entity for defining geopolitical units such as cities, districts, jurisdictions, or precincts, 
    for the purpose of associating contests, offices, vote counts, or other information with the geographies.
    See: https://developers.google.com/elections-data/reference/gp-unit
    """

    name: str
    type: ReportingUnitType
    contact_information: Optional[ContactInformation] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(
            self.object_id, self.name, str(self.type), self.contact_information
        )


@dataclass(eq=True, unsafe_hash=True)
class BallotStyle(ElectionObjectBase, CryptoHashable):
    """
    A BallotStyle works as a key to uniquely specify a set of contests. See also `ContestDescription`.
    """

    geopolitical_unit_ids: Optional[List[str]] = field(default=None)
    party_ids: Optional[List[str]] = field(default=None)
    image_uri: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(
            self.object_id, self.geopolitical_unit_ids, self.party_ids, self.image_uri
        )


@dataclass(eq=True, unsafe_hash=True)
class Party(ElectionObjectBase, CryptoHashable):
    """
    Use this entity to describe a political party that can then be referenced from other entities.
    See: https://developers.google.com/elections-data/reference/party
    """

    ballot_name: InternationalizedText = field(default=InternationalizedText())
    abbreviation: Optional[str] = field(default=None)
    color: Optional[str] = field(default=None)
    logo_uri: Optional[str] = field(default=None)

    def get_party_id(self) -> str:
        """
        Returns the object identifier associated with the Party.
        """
        return self.object_id

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(
            self.object_id,
            self.ballot_name,
            self.abbreviation,
            self.color,
            self.logo_uri,
        )


@dataclass(eq=True, unsafe_hash=True)
class Candidate(ElectionObjectBase, CryptoHashable):
    """
    Entity describing information about a candidate in a contest. 
    See: https://developers.google.com/elections-data/reference/candidate
    Note: The ElectionGuard Data Spec deviates from the NIST model in that 
    selections for any contest type are considered a "candidate".
    for instance, on a yes-no referendum contest, two `candidate` objects
    would be included in the model to represent the `affirmative` and `negative`
    selections for the contest.  See the wiki, readme's, and tests in this repo for more info
    """

    ballot_name: InternationalizedText = field(default=InternationalizedText())
    party_id: Optional[str] = field(default=None)
    image_uri: Optional[str] = field(default=None)
    is_write_in: Optional[bool] = field(default=None)

    def get_candidate_id(self) -> str:
        """
        Given a `Candidate`, returns a "candidate ID", which is used in other ElectionGuard structures.
        """
        return self.object_id

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(
            self.object_id, self.ballot_name, self.party_id, self.image_uri
        )


@dataclass(eq=True, unsafe_hash=True)
class SelectionDescription(ElectionObjectBase, CryptoHashable):
    """
    Data entity for the ballot selections in a contest, 
    for example linking candidates and parties to their vote counts.
    See: https://developers.google.com/elections-data/reference/ballot-selection
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    there is no difference for different types of selections. 
    The ElectionGuard Data Spec deviates from the NIST model in that
    `sequence_order` is a required field since it is used for ordering selections 
    in a contest to ensure various encryption primitives are deterministic.
    For a given election, the sequence of selections displayed to a user may be different
    however that information is not captured by default when encrypting a specific ballot.
    """

    candidate_id: str
    sequence_order: int
    """
    Used for ordering selections in a contest to ensure various encryption primitives are deterministic.
    The sequence order must be unique and should be representative of how the contests are represnted
    on a "master" ballot in an external system.  The sequence order is not required to be in the order 
    in which they are displayed to a voter.  Any acceptable range of integer values may be provided.
    """

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        return hash_elems(self.object_id, self.sequence_order, self.candidate_id)


@dataclass(unsafe_hash=True)
class ContestDescription(ElectionObjectBase, CryptoHashable):
    """
    Use this data entity for describing a contest and linking the contest 
    to the associated candidates and parties.
    See: https://developers.google.com/elections-data/reference/contest
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    `sequence_order` is a required field since it is used for ordering selections 
    in a contest to ensure various encryption primitives are deterministic.
    For a given election, the sequence of contests displayed to a user may be different
    however that information is not captured by default when encrypting a specific ballot.
    """

    electoral_district_id: str
    sequence_order: int
    """
    Used for ordering contests in a ballot to ensure various encryption primitives are deterministic.
    The sequence order must be unique and should be representative of how the contests are represnted
    on a "master" ballot in an external system.  The sequence order is not required to be in the order 
    in which they are displayed to a voter.  Any acceptable range of integer values may be provided.
    """

    vote_variation: VoteVariationType

    # Number of candidates that are elected in the contest ("n" of n-of-m).
    # Note: a referendum is considered a specific case of 1-of-m in ElectionGuard
    number_elected: int

    # Maximum number of votes/write-ins per voter in this contest. Used in cumulative voting
    # to indicate how many total votes a voter can spread around. In n-of-m elections, this will
    # be None.
    votes_allowed: Optional[int]

    # Name of the contest, not necessarily as it appears on the ballot.
    name: str

    # For associating a ballot selection for the contest, i.e., a candidate, a ballot measure.
    ballot_selections: List[SelectionDescription] = field(default_factory=lambda: [])

    # Title of the contest as it appears on the ballot.
    ballot_title: Optional[InternationalizedText] = field(default=None)

    # Subtitle of the contest as it appears on the ballot.
    ballot_subtitle: Optional[InternationalizedText] = field(default=None)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ContestDescription)
            and self.electoral_district_id == other.electoral_district_id
            and self.sequence_order == other.sequence_order
            and self.votes_allowed == other.votes_allowed
            and self.number_elected == other.number_elected
            and self.votes_allowed == other.votes_allowed
            and self.name == other.name
            and _list_eq(self.ballot_selections, other.ballot_selections)
            and self.ballot_title == other.ballot_title
            and self.ballot_subtitle == other.ballot_subtitle
        )

    def crypto_hash(self) -> ElementModQ:
        """
        Given a ContestDescription, deterministically derives a "hash" of that contest,
        suitable for use in ElectionGuard's "base hash" values, and for validating that
        either a plaintext or encrypted voted context and its corresponding contest
        description match up.
        """
        # remove any placeholders from the hash mechanism
        return hash_elems(
            self.object_id,
            self.sequence_order,
            self.electoral_district_id,
            str(self.vote_variation),
            self.ballot_title,
            self.ballot_subtitle,
            self.name,
            self.number_elected,
            self.votes_allowed,
            self.ballot_selections,
        )

    def is_valid(self) -> bool:
        """
        Check the validity of the contest object by verifying its data
        """
        contest_has_valid_number_elected = self.number_elected <= len(
            self.ballot_selections
        )
        contest_has_valid_votes_allowed = (
            self.votes_allowed is None or self.number_elected <= self.votes_allowed
        )

        # verify the candidate_ids, selection object_ids, and sequence_ids are unique
        candidate_ids: Set[str] = set()
        selection_ids: Set[str] = set()
        sequence_ids: Set[int] = set()
        selection_count = 0
        expected_selection_count = len(self.ballot_selections)

        for selection in self.ballot_selections:
            selection_count += 1
            # validate the object_id
            if selection.object_id not in selection_ids:
                selection_ids.add(selection.object_id)
            # validate the sequence_order
            if selection.sequence_order not in sequence_ids:
                sequence_ids.add(selection.sequence_order)
            # validate the candidate id
            if selection.candidate_id not in candidate_ids:
                candidate_ids.add(selection.candidate_id)

        selections_have_valid_candidate_ids = (
            len(candidate_ids) == expected_selection_count
        )
        selections_have_valid_selection_ids = (
            len(selection_ids) == expected_selection_count
        )
        selections_have_valid_sequence_ids = (
            len(sequence_ids) == expected_selection_count
        )

        success = (
            contest_has_valid_number_elected
            and contest_has_valid_votes_allowed
            and selections_have_valid_candidate_ids
            and selections_have_valid_selection_ids
            and selections_have_valid_sequence_ids
        )

        if not success:
            log_warning(
                "Contest %s failed validation check: %s",
                self.object_id,
                str(
                    {
                        "contest_has_valid_number_elected": contest_has_valid_number_elected,
                        "contest_has_valid_votes_allowed": contest_has_valid_votes_allowed,
                        "selections_have_valid_candidate_ids": selections_have_valid_candidate_ids,
                        "selections_have_valid_selection_ids": selections_have_valid_selection_ids,
                        "selections_have_valid_sequence_ids": selections_have_valid_sequence_ids,
                    }
                ),
            )

        return success


@dataclass(eq=True, unsafe_hash=True)
class CandidateContestDescription(ContestDescription):
    """
    Use this entity to describe a contest that involves selecting one or more candidates.
    See: https://developers.google.com/elections-data/reference/contest
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    this subclass is used purely for convenience 
    """

    primary_party_ids: List[str] = field(default_factory=lambda: [])


@dataclass(eq=True, unsafe_hash=True)
class ReferendumContestDescription(ContestDescription):
    """
    Use this entity to describe a contest that involves selecting exactly one 'candidate'.
    See: https://developers.google.com/elections-data/reference/contest
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    this subclass is used purely for convenience
    """

    pass


@dataclass(eq=True, unsafe_hash=True)
class ContestDescriptionWithPlaceholders(ContestDescription):
    """
    ContestDescriptionWithPlaceholders is a `ContestDescription` with ElectionGuard `placeholder_selections`.
    (The ElectionGuard spec requires for n-of-m elections that there be *exactly* n counters that are one
    with the rest zero, so if a voter deliberately undervotes, one or more of the placeholder counters will
    become one. This allows the `ConstantChaumPedersenProof` to verify correctly for undervoted contests.)
    """

    placeholder_selections: List[SelectionDescription] = field(
        default_factory=lambda: []
    )

    def is_valid(self) -> bool:
        """
        Checks is contest description is valid
        :return: true if valid
        """
        contest_description_validates = super().is_valid()
        return (
            contest_description_validates
            and len(self.placeholder_selections) == self.number_elected
        )

    def is_placeholder(self, selection: SelectionDescription) -> bool:
        """
        Checks is contest description is placeholder
        :return: true if placeholder
        """
        return selection in self.placeholder_selections

    def selection_for(self, selection_id: str) -> Optional[SelectionDescription]:
        """
        Gets the description for a particular id
        :param selection_id: Id of Selection
        :return: description
        """
        matching_selections = list(
            filter(lambda i: i.object_id == selection_id, self.ballot_selections)
        )

        if any(matching_selections):
            return matching_selections[0]

        matching_placeholders = list(
            filter(lambda i: i.object_id == selection_id, self.placeholder_selections)
        )

        if any(matching_placeholders):
            return matching_placeholders[0]
        else:
            return None


@dataclass(unsafe_hash=True)
class ElectionDescription(Serializable, CryptoHashable):
    """
    Use this entity for defining the structure of the election and associated 
    information such as candidates, contests, and vote counts.  This class is
    based on the NIST Election Common Standard Data Specification.  Some deviations
    from the standard exist.

    This structure is considered an immutable input object and should not be changed
    through the course of an election, as it's hash representation is the basis for all
    other hash representations within an ElectionGuard election context.

    See: https://developers.google.com/elections-data/reference/election
    """

    election_scope_id: str
    type: ElectionType
    start_date: datetime
    end_date: datetime
    geopolitical_units: List[GeopoliticalUnit]
    parties: List[Party]
    candidates: List[Candidate]
    contests: List[ContestDescription]
    ballot_styles: List[BallotStyle]
    name: Optional[InternationalizedText] = field(default=None)
    contact_information: Optional[ContactInformation] = field(default=None)

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, ElectionDescription)
            and self.election_scope_id == other.election_scope_id
            and self.type == other.type
            and self.start_date == other.start_date
            and self.end_date == other.end_date
            and _list_eq(self.geopolitical_units, other.geopolitical_units)
            and _list_eq(self.parties, other.parties)
            and _list_eq(self.candidates, other.candidates)
            and _list_eq(self.contests, other.contests)
            and _list_eq(self.ballot_styles, other.ballot_styles)
            and self.name == other.name
            and self.contact_information == other.contact_information
        )

    def crypto_hash(self) -> ElementModQ:
        """
        Returns a hash of the metadata components of the election
        """

        return hash_elems(
            self.election_scope_id,
            str(self.type),
            self.start_date.isoformat(),
            self.end_date.isoformat(),
            self.name,
            self.contact_information,
            self.geopolitical_units,
            self.parties,
            self.parties,
            self.contests,
            self.ballot_styles,
        )

    def is_valid(self) -> bool:
        """
        Verifies the dataset to ensure it is well-formed
        """
        gp_unit_ids: Set[str] = set()
        ballot_style_ids: Set[str] = set()
        party_ids: Set[str] = set()
        candidate_ids: Set[str] = set()
        contest_ids: Set[str] = set()
        selection_ids: Set[str] = set()

        # Validate GP Units
        for gp_unit in self.geopolitical_units:
            if gp_unit.object_id not in gp_unit_ids:
                gp_unit_ids.add(gp_unit.object_id)

        # fail if there are duplicates
        geopolitical_units_valid = len(gp_unit_ids) == len(self.geopolitical_units)

        # Validate Ballot Styles
        ballot_styles_have_valid_gp_unit_ids = True

        for style in self.ballot_styles:
            if style.object_id not in ballot_style_ids:
                ballot_style_ids.add(style.object_id)
            if style.geopolitical_unit_ids is None:
                ballot_styles_have_valid_gp_unit_ids = False
                break
            # validate associated gp unit ids
            for gp_unit_id in style.geopolitical_unit_ids:
                ballot_styles_have_valid_gp_unit_ids = (
                    ballot_styles_have_valid_gp_unit_ids and gp_unit_id in gp_unit_ids
                )

        ballot_styles_valid = (
            len(ballot_style_ids) == len(self.ballot_styles)
            and ballot_styles_have_valid_gp_unit_ids
        )

        # Validate Parties
        for party in self.parties:
            if party.object_id not in party_ids:
                party_ids.add(party.object_id)

        parties_valid = len(party_ids) == len(self.parties)

        # Validate Candidates
        candidates_have_valid_party_ids = True

        for candidate in self.candidates:
            if candidate.object_id not in candidate_ids:
                candidate_ids.add(candidate.object_id)
            # validate the associated party id
            candidates_have_valid_party_ids = candidates_have_valid_party_ids and (
                candidate.party_id is None or candidate.party_id in party_ids
            )

        candidates_have_valid_length = len(candidate_ids) == len(self.candidates)
        candidates_valid = (
            candidates_have_valid_length and candidates_have_valid_party_ids
        )

        # Validate Contests
        contests_validate_their_properties = True
        contests_have_valid_electoral_district_id = True
        candidate_contests_have_valid_party_ids = True

        contest_sequence_ids: Set[int] = set()

        for contest in self.contests:

            contests_validate_their_properties = (
                contests_validate_their_properties and contest.is_valid()
            )

            if contest.object_id not in contest_ids:
                contest_ids.add(contest.object_id)

            # validate the sequence order
            if contest.sequence_order not in contest_sequence_ids:
                contest_sequence_ids.add(contest.sequence_order)

            # validate the associated gp unit id
            contests_have_valid_electoral_district_id = (
                contests_have_valid_electoral_district_id
                and contest.electoral_district_id in gp_unit_ids
            )

            if isinstance(contest, CandidateContestDescription):
                candidate_contest = cast(CandidateContestDescription, contest)
                if candidate_contest.primary_party_ids is not None:
                    for primary_party_id in candidate_contest.primary_party_ids:
                        # validate the party ids
                        candidate_contests_have_valid_party_ids = (
                            candidate_contests_have_valid_party_ids
                            and primary_party_id in party_ids
                        )

        # TODO: ISSUE #55: verify that the contest sequence order set is in the proper order

        contests_have_valid_object_ids = len(contest_ids) == len(self.contests)
        contests_have_valid_sequence_ids = len(contest_sequence_ids) == len(
            self.contests
        )
        contests_valid = (
            contests_have_valid_object_ids
            and contests_have_valid_sequence_ids
            and contests_validate_their_properties
            and contests_have_valid_electoral_district_id
            and candidate_contests_have_valid_party_ids
        )

        success = (
            geopolitical_units_valid
            and ballot_styles_valid
            and parties_valid
            and candidates_valid
            and contests_valid
        )

        if not success:
            log_warning(
                "Election failed validation check: is_valid: %s",
                str(
                    {
                        "geopolitical_units_valid": geopolitical_units_valid,
                        "ballot_styles_valid": ballot_styles_valid,
                        "ballot_styles_have_valid_gp_unit_ids": ballot_styles_have_valid_gp_unit_ids,
                        "parties_valid": parties_valid,
                        "candidates_valid": candidates_valid,
                        "candidates_have_valid_length": candidates_have_valid_length,
                        "candidates_have_valid_party_ids": candidates_have_valid_party_ids,
                        "contests_valid": contests_valid,
                        "contests_have_valid_object_ids": contests_have_valid_object_ids,
                        "contests_have_valid_sequence_ids": contests_have_valid_sequence_ids,
                        "contests_validate_their_properties": contests_validate_their_properties,
                        "contests_have_valid_electoral_district_id": contests_have_valid_electoral_district_id,
                        "candidate_contests_have_valid_party_ids": candidate_contests_have_valid_party_ids,
                    }
                ),
            )
        return success


@dataclass(eq=True, unsafe_hash=True)
class InternalElectionDescription(object):
    """
    `InternalElectionDescription` is a subset of the `ElectionDescription` structure that specifies
    the components that ElectionGuard uses for conducting an election.  The key component is the
    `contests` collection, which applies placeholder selections to the `ElectionDescription` contests
    """

    description: InitVar[ElectionDescription] = None

    geopolitical_units: List[GeopoliticalUnit] = field(init=False)

    contests: List[ContestDescriptionWithPlaceholders] = field(init=False)

    ballot_styles: List[BallotStyle] = field(init=False)

    description_hash: ElementModQ = field(init=False)

    def __post_init__(self, description: ElectionDescription) -> None:
        object.__setattr__(self, "description_hash", description.crypto_hash())
        object.__setattr__(self, "geopolitical_units", description.geopolitical_units)
        object.__setattr__(self, "ballot_styles", description.ballot_styles)
        object.__setattr__(
            self, "contests", self._generate_contests_with_placeholders(description)
        )

    def contest_for(
        self, contest_id: str
    ) -> Optional[ContestDescriptionWithPlaceholders]:
        """
        Get contest by id
        :param contest_id: Contest id
        :return: Contest description or none
        """
        matching_contests = list(
            filter(lambda i: i.object_id == contest_id, self.contests)
        )

        if any(matching_contests):
            return matching_contests[0]
        else:
            return None

    def get_ballot_style(self, ballot_style_id: str) -> BallotStyle:
        """
        Get a ballot style for a specified ballot_style_id
        """
        style = list(
            filter(lambda i: i.object_id == ballot_style_id, self.ballot_styles)
        )[0]
        return style

    def get_contests_for(
        self, ballot_style_id: str
    ) -> List[ContestDescriptionWithPlaceholders]:
        """
        Get contests for a ballot style
        :param ballot_style_id: ballot style id
        :return: contest descriptions
        """
        style = self.get_ballot_style(ballot_style_id)
        if style.geopolitical_unit_ids is None:
            return list()
        gp_unit_ids = [gp_unit_id for gp_unit_id in style.geopolitical_unit_ids]
        contests = list(
            filter(lambda i: i.electoral_district_id in gp_unit_ids, self.contests)
        )
        return contests

    def _generate_contests_with_placeholders(
        self, description: ElectionDescription
    ) -> List[ContestDescriptionWithPlaceholders]:
        """
        For each contest, append the `number_elected` number 
        of placeholder selections to the end of the contest collection
        """
        contests: List[ContestDescriptionWithPlaceholders] = list()
        for contest in description.contests:
            placeholder_selections = generate_placeholder_selections_from(
                contest, contest.number_elected
            )
            contests.append(
                contest_description_with_placeholders_from(
                    contest, placeholder_selections
                )
            )

        return contests


@dataclass(eq=True, unsafe_hash=True)
class ElectionConstants(Serializable):
    """
    The constants for mathematical functions during the election. 
    """

    large_prime = P
    """large prime or p"""

    small_prime = Q
    """small prime or q"""

    cofactor = R
    """cofactor or r"""

    generator = G
    """generator or g"""


@dataclass(eq=True, unsafe_hash=True)
class CiphertextElectionContext(Serializable):
    """
    `CiphertextElectionContext` is the ElectionGuard representation of a specific election
    Note: The ElectionGuard Data Spec deviates from the NIST model in that
    this object includes fields that are populated in the course of encrypting an election
    Specifically, `crypto_base_hash`, `crypto_extended_base_hash` and `elgamal_public_key`
    are populated with election-specific information necessary for encrypting the election.
    Refer to the [Electionguard Specification](https://github.com/microsoft/electionguard) for more information.

    To make an instance of this class, don't construct it directly. Use
    `make_ciphertext_election_context` instead.
    """

    number_of_guardians: int
    """
    The number of guardians necessary to generate the public key
    """
    quorum: int
    """
    The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    """

    # the `joint public key (K)` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    elgamal_public_key: ElementModP

    # The hash of the election metadata
    description_hash: ElementModQ

    # the `base hash code (𝑄)` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    crypto_base_hash: ElementModQ

    # the `extended base hash code (𝑄')` in the [ElectionGuard Spec](https://github.com/microsoft/electionguard/wiki)
    crypto_extended_base_hash: ElementModQ


def make_ciphertext_election_context(
    number_of_guardians: int,
    quorum: int,
    elgamal_public_key: ElementModP,
    description_hash: ElementModQ,
) -> CiphertextElectionContext:
    """
    Makes a CiphertextElectionContext object.

    :param number_of_guardians: The number of guardians necessary to generate the public key
    :param quorum: The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    :param elgamal_public_key: the public key of the election
    :param description_hash: the hash of the election metadata
    """

    # What's a crypto_base_hash?
    # The metadata of this object are hashed together with the
    # - prime modulus (𝑝),
    # - subgroup order (𝑞),
    # - generator (𝑔),
    # - number of guardians (𝑛),
    # - decryption threshold value (𝑘),
    # to form a base hash code (𝑄) which will be incorporated
    # into every subsequent hash computation in the election.

    # What's a crypto_extended_base_hash?
    # Once the baseline parameters have been produced and confirmed,
    # all of the public guardian commitments 𝐾𝑖,𝑗 are hashed together
    # with the base hash 𝑄 to form an extended base hash 𝑄' that will
    # form the basis of subsequent hash computations.

    crypto_base_hash = hash_elems(
        P, Q, G, number_of_guardians, quorum, description_hash
    )
    crypto_extended_base_hash = hash_elems(crypto_base_hash, elgamal_public_key)
    return CiphertextElectionContext(
        number_of_guardians=number_of_guardians,
        quorum=quorum,
        elgamal_public_key=elgamal_public_key,
        description_hash=description_hash,
        crypto_base_hash=crypto_base_hash,
        crypto_extended_base_hash=crypto_extended_base_hash,
    )


def contest_description_with_placeholders_from(
    description: ContestDescription, placeholders: List[SelectionDescription]
) -> ContestDescriptionWithPlaceholders:
    """
    Generates a placeholder selection description
    :param description: contest description
    :param placeholders: list of placeholder descriptions of selections
    :return: a SelectionDescription or None
    """
    return ContestDescriptionWithPlaceholders(
        object_id=description.object_id,
        electoral_district_id=description.electoral_district_id,
        sequence_order=description.sequence_order,
        vote_variation=description.vote_variation,
        number_elected=description.number_elected,
        votes_allowed=description.votes_allowed,
        name=description.name,
        ballot_selections=description.ballot_selections,
        ballot_title=description.ballot_title,
        ballot_subtitle=description.ballot_subtitle,
        placeholder_selections=placeholders,
    )


def generate_placeholder_selection_from(
    contest: ContestDescription, use_sequence_id: Optional[int] = None
) -> Optional[SelectionDescription]:
    """
    Generates a placeholder selection description that is unique so it can be hashed

    :param use_sequence_id: an optional integer unique to the contest identifying this selection's place in the contest
    :return: a SelectionDescription or None
    """
    sequence_ids = [selection.sequence_order for selection in contest.ballot_selections]
    if use_sequence_id is None:
        # if no sequence order is specified, take the max
        use_sequence_id = max(*sequence_ids) + 1
    elif use_sequence_id in sequence_ids:
        log_warning(
            f"mismatched placeholder selection {use_sequence_id} already exists"
        )
        return None

    placeholder_object_id = f"{contest.object_id}-{use_sequence_id}"
    return SelectionDescription(
        f"{placeholder_object_id}-placeholder",
        f"{placeholder_object_id}-candidate",
        use_sequence_id,
    )


def generate_placeholder_selections_from(
    contest: ContestDescription, count: int
) -> List[SelectionDescription]:
    """
    Generates the specified number of placeholder selections in ascending sequence order from the max selection sequence orderf

    :param contest: ContestDescription for input
    :param count: optionally specify a number of placeholders to generate
    :return: a collection of `SelectionDescription` objects, which may be empty
    """
    max_sequence_order = max(
        [selection.sequence_order for selection in contest.ballot_selections]
    )
    selections: List[SelectionDescription] = list()
    for i in range(count):
        sequence_order = max_sequence_order + 1 + i
        selections.append(
            get_optional(generate_placeholder_selection_from(contest, sequence_order))
        )
    return selections
