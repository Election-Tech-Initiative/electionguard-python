from dataclasses import dataclass, field, InitVar
from datetime import datetime
from enum import Enum, unique
from typing import Dict, cast, List, Optional, Set, Any

from .election_object_base import ElectionObjectBase, OrderedObjectBase, list_eq
from .group import ElementModQ
from .hash import CryptoHashable, hash_elems
from .logs import log_warning
from .utils import get_optional, to_iso_date_string


@unique
class ElectionType(Enum):
    """
    enumerations for the `ElectionReport` entity
    see: https://developers.google.com/elections-data/reference/election-type
    """

    unknown = "unknown"
    general = "general"
    partisan_primary_closed = "partisan_primary_closed"
    partisan_primary_open = "partisan_primary_open"
    primary = "primary"
    runoff = "runoff"
    special = "special"
    other = "other"


@unique
class ReportingUnitType(Enum):
    """
    Enumeration for the type of geopolitical unit
    see: https://developers.google.com/elections-data/reference/reporting-unit-type
    """

    unknown = "unknown"
    ballot_batch = "ballot_batch"
    ballot_style_area = "ballot_style_area"
    borough = "borough"
    city = "city"
    city_council = "city_council"
    combined_precinct = "combined_precinct"
    congressional = "congressional"
    country = "country"
    county = "county"
    county_council = "county_council"
    drop_box = "drop_box"
    judicial = "judicial"
    municipality = "municipality"
    polling_place = "polling_place"
    precinct = "precinct"
    school = "school"
    special = "special"
    split_precinct = "split_precinct"
    state = "state"
    state_house = "state_house"
    state_senate = "state_senate"
    township = "township"
    utility = "utility"
    village = "village"
    vote_center = "vote_center"
    ward = "ward"
    water = "water"
    other = "other"


@unique
class VoteVariationType(Enum):
    """
    Enumeration for contest algorithm or rules in the `Contest` entity
    see: https://developers.google.com/elections-data/reference/vote-variation
    """

    one_of_m = "one_of_m"
    approval = "approval"
    borda = "borda"
    cumulative = "cumulative"
    majority = "majority"
    n_of_m = "n_of_m"
    plurality = "plurality"
    proportional = "proportional"
    range = "range"
    rcv = "rcv"
    super_majority = "super_majority"
    other = "other"


SUPPORTED_VOTE_VARIATIONS = [
    VoteVariationType.one_of_m,
    VoteVariationType.approval,
    VoteVariationType.majority,
    VoteVariationType.n_of_m,
    VoteVariationType.plurality,
    VoteVariationType.super_majority,
]

# pylint: disable=super-init-not-called
@dataclass(eq=True, unsafe_hash=True)
class AnnotatedString(CryptoHashable):
    """
    Use this as a type for character strings.
    See: https://developers.google.com/elections-data/reference/annotated-string
    """

    annotation: str = field(default="")
    value: str = field(default="")

    # explicit `__init__` added as workaround for https://bugs.python.org/issue45081
    # can potentially be removed with future python version >3.9.7
    def __init__(
        self,
        annotation: str = "",
        value: str = "",
    ):
        self.annotation = annotation
        self.value = value

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        hash = hash_elems(self.annotation, self.value)
        return hash


# pylint: disable=super-init-not-called
@dataclass(eq=True, unsafe_hash=True)
class Language(CryptoHashable):
    """
    The ISO-639 language
    see: https://en.wikipedia.org/wiki/ISO_639
    """

    value: str
    language: str = field(default="en")

    # explicit `__init__` added as workaround for https://bugs.python.org/issue45081
    # can potentially be removed with future python version >3.9.7
    def __init__(
        self,
        value: str,
        language: str = "en",
    ):
        self.value = value
        self.language = language

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        hash = hash_elems(self.value, self.language)
        return hash


# pylint: disable=super-init-not-called
@dataclass(eq=True, unsafe_hash=True)
class InternationalizedText(CryptoHashable):
    """
    Data entity used to represent multi-national text. Use when text on a ballot contains multi-national text.
    See: https://developers.google.com/elections-data/reference/internationalized-text
    """

    text: List[Language] = field(default_factory=lambda: [])

    # explicit `__init__` added as workaround for https://bugs.python.org/issue45081
    # can potentially be removed with future python version >3.9.7
    def __init__(
        self,
        text: List[Language] = None,
    ):
        self.text = text if text else []

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        hash = hash_elems(self.text)
        return hash


# pylint: disable=super-init-not-called
@dataclass(eq=True, unsafe_hash=True)
class ContactInformation(CryptoHashable):
    """
    For defining contact information about objects such as persons, boards of authorities, and organizations.
    See: https://developers.google.com/elections-data/reference/contact-information
    """

    address_line: Optional[List[str]] = field(default=None)
    email: Optional[List[AnnotatedString]] = field(default=None)
    phone: Optional[List[AnnotatedString]] = field(default=None)
    name: Optional[str] = field(default=None)

    # explicit `__init__` added as workaround for https://bugs.python.org/issue45081
    # can potentially be removed with future python version >3.9.7
    def __init__(
        self,
        address_line: Optional[List[str]] = None,
        email: Optional[List[AnnotatedString]] = None,
        phone: Optional[List[AnnotatedString]] = None,
        name: Optional[str] = None,
    ):
        self.address_line = address_line
        self.email = email
        self.phone = phone
        self.name = name

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        hash = hash_elems(self.name, self.address_line, self.email, self.phone)
        return hash


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
        hash = hash_elems(
            self.object_id, self.name, str(self.type.name), self.contact_information
        )
        return hash


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
        hash = hash_elems(
            self.object_id, self.geopolitical_unit_ids, self.party_ids, self.image_uri
        )
        return hash


@dataclass(eq=True, unsafe_hash=True)
class Party(ElectionObjectBase, CryptoHashable):
    """
    Use this entity to describe a political party that can then be referenced from other entities.
    See: https://developers.google.com/elections-data/reference/party
    """

    name: InternationalizedText = field(default=InternationalizedText())
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
        hash = hash_elems(
            self.object_id,
            self.name,
            self.abbreviation,
            self.color,
            self.logo_uri,
        )
        return hash


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

    name: InternationalizedText = field(default=InternationalizedText())
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
        hash = hash_elems(self.object_id, self.name, self.party_id, self.image_uri)
        return hash


@dataclass(eq=True, unsafe_hash=True)
class SelectionDescription(OrderedObjectBase, CryptoHashable):
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

    def crypto_hash(self) -> ElementModQ:
        """
        A hash representation of the object
        """
        hash = hash_elems(self.object_id, self.sequence_order, self.candidate_id)
        return hash


# pylint: disable=too-many-instance-attributes
@dataclass(unsafe_hash=True)
class ContestDescription(OrderedObjectBase, CryptoHashable):
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
            and self.vote_variation == other.vote_variation
            and self.number_elected == other.number_elected
            and self.votes_allowed == other.votes_allowed
            and self.name == other.name
            and list_eq(self.ballot_selections, other.ballot_selections)
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
        hash = hash_elems(
            self.object_id,
            self.sequence_order,
            self.electoral_district_id,
            str(self.vote_variation.name),
            self.ballot_title,
            self.ballot_subtitle,
            self.name,
            self.number_elected,
            self.votes_allowed,
            self.ballot_selections,
        )
        return hash

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

        contest_has_supported_vote_variation = (
            self.vote_variation in SUPPORTED_VOTE_VARIATIONS
        )

        success = (
            contest_has_valid_number_elected
            and contest_has_valid_votes_allowed
            and selections_have_valid_candidate_ids
            and selections_have_valid_selection_ids
            and selections_have_valid_sequence_ids
            and contest_has_supported_vote_variation
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
                        "contest_has_supported_vote_variation": contest_has_supported_vote_variation,
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
        return None


class SpecVersion(Enum):
    """Specify ElectionGuard Versions"""

    EG0_95 = "v0.95"
    EG1_0 = "1.0"


# pylint: disable=too-many-instance-attributes,super-init-not-called
@dataclass(unsafe_hash=True)
class Manifest(CryptoHashable):
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
    spec_version: SpecVersion
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

    # explicit `__init__` added as workaround for https://bugs.python.org/issue45081
    # can potentially be removed with future python version >3.9.7
    def __init__(
        self,
        election_scope_id: str,
        spec_version: SpecVersion,
        type: ElectionType,
        start_date: datetime,
        end_date: datetime,
        geopolitical_units: List[GeopoliticalUnit],
        parties: List[Party],
        candidates: List[Candidate],
        contests: List[ContestDescription],
        ballot_styles: List[BallotStyle],
        name: Optional[InternationalizedText] = None,
        contact_information: Optional[ContactInformation] = None,
    ):
        self.election_scope_id = election_scope_id
        self.spec_version = spec_version
        self.type = type
        self.start_date = start_date
        self.end_date = end_date
        self.geopolitical_units = geopolitical_units
        self.parties = parties
        self.candidates = candidates
        self.contests = contests
        self.ballot_styles = ballot_styles
        self.name = name
        self.contact_information = contact_information

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Manifest)
            and self.election_scope_id == other.election_scope_id
            and self.type == other.type
            and self.start_date == other.start_date
            and self.end_date == other.end_date
            and list_eq(self.geopolitical_units, other.geopolitical_units)
            and list_eq(self.parties, other.parties)
            and list_eq(self.candidates, other.candidates)
            and list_eq(self.contests, other.contests)
            and list_eq(self.ballot_styles, other.ballot_styles)
            and self.name == other.name
            and self.contact_information == other.contact_information
        )

    def crypto_hash(self) -> ElementModQ:
        """
        Returns a hash of the metadata components of the election
        """
        hash = hash_elems(
            self.election_scope_id,
            str(self.type.name),
            to_iso_date_string(self.start_date),
            to_iso_date_string(self.end_date),
            self.name,
            self.contact_information,
            self.geopolitical_units,
            self.parties,
            self.contests,
            self.ballot_styles,
        )
        return hash

    def is_valid(self) -> bool:
        """
        Verifies the dataset to ensure it is well-formed
        """
        gp_unit_ids: Set[str] = set()
        ballot_style_ids: Set[str] = set()
        party_ids: Set[str] = set()
        candidate_ids: Set[str] = set()
        contest_ids: Set[str] = set()

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

    def _get_candidate_name(self, candidate: Candidate, lang: str) -> str:
        if candidate.is_write_in:
            return "Write-In"
        return get_i8n_value(candidate.name, lang, candidate.object_id)

    def _get_candidate_names(self, lang: str) -> Dict[str, str]:
        return {
            candidate.object_id: self._get_candidate_name(candidate, lang)
            for candidate in self.candidates
        }

    def _get_selections_with_candidate_id(self) -> Dict[str, str]:
        selections: Dict[str, str] = {}
        for contest in self.contests:
            for selection in contest.ballot_selections:
                selections.update({selection.object_id: selection.candidate_id})
        return selections

    def _replace_candidate_ids_with_names(
        self, selections: Dict[str, str], candidates: Dict[str, str]
    ) -> None:
        for (selection_id, candidate_id) in selections.items():
            candidate_name = candidates.get(candidate_id)
            if candidate_name is not None:
                selections.update({selection_id: candidate_name})

    def get_selection_names(self, lang: str) -> Dict[str, str]:
        """
        Retrieves a dictionary whose keys are all selection id's and whose values are
        those selection's candidate names in the supplied language if available
        """
        candidates = self._get_candidate_names(lang)
        selections = self._get_selections_with_candidate_id()
        self._replace_candidate_ids_with_names(selections, candidates)
        return selections

    def get_contest_names(self) -> Dict[str, str]:
        """
        Retrieves a dictionary whose keys are all contest id's and whose values are
        those contest's names
        """

        return {contest.object_id: contest.name for contest in self.contests}

    def get_name(self) -> str:
        def get_first_value(text: Optional[InternationalizedText]) -> str:
            return "" if text is None else text.text[0].value

        return get_first_value(self.name)


@dataclass(eq=True, unsafe_hash=True)
class InternalManifest:
    """
    `InternalManifest` is a subset of the `Manifest` structure that specifies
    the components that ElectionGuard uses for conducting an election.  The key component is the
    `contests` collection, which applies placeholder selections to the `Manifest` contests
    """

    manifest: InitVar[Manifest] = None

    geopolitical_units: List[GeopoliticalUnit] = field(init=False)

    contests: List[ContestDescriptionWithPlaceholders] = field(init=False)

    ballot_styles: List[BallotStyle] = field(init=False)

    manifest_hash: ElementModQ = field(init=False)

    def __post_init__(self, manifest: Manifest) -> None:
        object.__setattr__(self, "manifest_hash", manifest.crypto_hash())
        object.__setattr__(self, "geopolitical_units", manifest.geopolitical_units)
        object.__setattr__(self, "ballot_styles", manifest.ballot_styles)
        object.__setattr__(
            self, "contests", self._generate_contests_with_placeholders(manifest)
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
            return []
        # pylint: disable=unnecessary-comprehension
        gp_unit_ids = [gp_unit_id for gp_unit_id in style.geopolitical_unit_ids]
        contests = list(
            filter(lambda i: i.electoral_district_id in gp_unit_ids, self.contests)
        )
        return contests

    @staticmethod
    def _generate_contests_with_placeholders(
        manifest: Manifest,
    ) -> List[ContestDescriptionWithPlaceholders]:
        """
        For each contest, append the `number_elected` number
        of placeholder selections to the end of the contest collection
        """
        contests: List[ContestDescriptionWithPlaceholders] = []
        for contest in manifest.contests:
            placeholder_selections = generate_placeholder_selections_from(
                contest, contest.number_elected
            )
            contests.append(
                contest_description_with_placeholders_from(
                    contest, placeholder_selections
                )
            )

        return contests


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
        use_sequence_id,
        f"{placeholder_object_id}-candidate",
    )


def generate_placeholder_selections_from(
    contest: ContestDescription, count: int
) -> List[SelectionDescription]:
    """
    Generates the specified number of placeholder selections in
    ascending sequence order from the max selection sequence orderf

    :param contest: ContestDescription for input
    :param count: optionally specify a number of placeholders to generate
    :return: a collection of `SelectionDescription` objects, which may be empty
    """
    max_sequence_order = max(
        [selection.sequence_order for selection in contest.ballot_selections]
    )
    selections: List[SelectionDescription] = []
    for i in range(count):
        sequence_order = max_sequence_order + 1 + i
        selections.append(
            get_optional(generate_placeholder_selection_from(contest, sequence_order))
        )
    return selections


def get_i8n_value(name: InternationalizedText, lang: str, default_val: str) -> str:
    query = (t.value for t in name.text if t.language == lang)
    result = next(query, "")
    return default_val if result == "" else result
