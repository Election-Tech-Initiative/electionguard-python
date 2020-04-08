from dataclasses import dataclass, field
from enum import Enum, unique
from datetime import datetime, timezone
from typing import Optional, List, TypeVar, Generic, Set, Union

from .logs import log_warning

from .is_valid import IsValid
from .serializable import Serializable

@unique
class ElectionType(Enum):
    general = 1
    partisan_primary_closed = 2
    partisan_primary_open = 3
    primary = 4
    runoff = 5
    special = 6
    other = 7
    unknown = 8

@unique
class ReportingUnitType(Enum):
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
    unknown = 29

@unique
class VoteVariationType(Enum):
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
    unknown = 13

@dataclass
class AnnotatedString(Serializable):
    """
    """
    annotation: str = field(default="")
    value: str = field(default="")

@dataclass
class Language(Serializable):
    """
    Internationalized Text
    """
    value: str
    language: str = field(default="en")

@dataclass
class InternationalizedText(Serializable):
    """
    """
    text: List[Language] = field(default_factory=lambda: [])

@dataclass
class ContactInformation(Serializable):
    """
    """
    address_line: Optional[List[str]] = field(default=None)
    email: Optional[List[AnnotatedString]] = field(default=None)
    phone: Optional[List[AnnotatedString]] = field(default=None)
    name: Optional[str] = field(default=None)

@dataclass
class GeopoliticalUnit(Serializable):
    """
    """
    object_id: str
    name: str
    type: ReportingUnitType
    contact_information: Optional[ContactInformation] = field(default=None)

@dataclass
class BallotStyle(Serializable):
    """
    """
    object_id: str
    geopolitical_unit_ids: Optional[List[str]] = field(default=None)
    party_ids: Optional[List[str]] = field(default=None)
    image_uri: Optional[str] = field(default=None)

@dataclass
class Party(Serializable):
    """
    """
    object_id: str
    ballot_name: InternationalizedText = field(default=InternationalizedText())
    abbreviation: Optional[str] = field(default=None)
    color: Optional[str] = field(default=None)
    logoUri: Optional[str] = field(default=None)

@dataclass
class Candidate(Serializable):
    """
    Candidate
    """
    object_id: str
    ballot_name: InternationalizedText = field(default=InternationalizedText())
    party_id: Optional[str] = field(default=None)
    imageUri: Optional[str] = field(default=None)

@dataclass
class Selection(Serializable):
    """
    typed selection object
    """
    object_id: str

@dataclass
class ManifestSelection(Selection):
    candidate_id: str
    sequence_order: int

@dataclass
class Contest(Serializable):
    object_id: str

@dataclass
class ManifestContest(Contest):
    """
    """
    electoral_district_id: str
    vote_variation: VoteVariationType

    """
    The number of candidate seats 
    """
    number_elected: int
    ballot_selections: List[ManifestSelection] = field(default_factory=lambda: [])
    ballot_title: InternationalizedText = field(default=InternationalizedText())
    ballot_subtitle: Optional[InternationalizedText] = field(default=None)
    name: Optional[str] = field(default=None)
    sequence_order: Optional[int] = field(default=None)
    
    """
    Indicates the number of individual votes a voter has.
    If no value is present, assumed to be number elected
    """
    votes_allowed: Optional[int] = field(default=None)

@dataclass
class CandidateContest(ManifestContest):
    """
    """
    primary_party_ids: List[str] = field(default_factory=lambda: [])

@dataclass
class ReferendumContest(ManifestContest):
    """
    """
    pass

DerivedContestType = Union[CandidateContest, ReferendumContest]

@dataclass
class Election(Serializable, IsValid):
    """
    """
    election_scope_id: str
    type: ElectionType
    start_date: datetime
    end_date: datetime
    geopolitical_units: List[GeopoliticalUnit]
    parties: List[Party]
    candidates: List[Candidate]
    contests: List[DerivedContestType]
    ballot_styles: List[BallotStyle]
    name: Optional[InternationalizedText] = field(default=None)
    contact_information: Optional[ContactInformation] = field(default=None)

    crypto_hash: Optional[str] = field(default=None)
    crypto_extended_hash: Optional[str] = field(default=None)

    def is_valid(self) -> bool:
        """
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
        geopolitical_units_valid = len(gp_unit_ids) is len(self.geopolitical_units)

        # Validate Ballot Styles
        ballot_styles_have_valid_gp_unit_ids = True

        for style in self.ballot_styles:
            if style.object_id not in ballot_style_ids:
                ballot_style_ids.add(style.object_id)
            # validate associated gp unit ids
            for gp_unit_id in style.geopolitical_unit_ids:
                ballot_styles_have_valid_gp_unit_ids = ballot_styles_have_valid_gp_unit_ids \
                and gp_unit_id in gp_unit_ids

        ballot_styles_valid = len(ballot_style_ids) is len(self.ballot_styles) \
            and ballot_styles_have_valid_gp_unit_ids

        # Validate Parties
        for party in self.parties:
            if party.object_id not in party_ids:
                party_ids.add(party.object_id)

        parties_valid = len(party_ids) is len(self.parties)

        # Validate Candidates
        candidates_have_valid_party_ids = True

        for candidate in self.candidates:
            if candidate.object_id not in candidate_ids:
                candidate_ids.add(candidate.object_id)
            # validate the associated party id
            candidates_have_valid_party_ids = candidates_have_valid_party_ids \
                and (candidate.party_id is None or candidate.party_id in party_ids)

        candidates_valid = len(candidate_ids) is len(self.candidates) \
             and candidates_have_valid_party_ids

        # Validate Contests
        contests_have_valid_electoral_district_id = True
        contests_have_valid_number_elected = True
        contests_have_valid_number_votes_allowed = True

        candidate_contests_have_valid_party_ids = True

        contest_sequence_ids: Set[int] = set()

        for contest in self.contests:
            if contest.object_id not in contest_ids:
                contest_ids.add(contest.object_id)
            # validate the sequence order
            if contest.sequence_order not in contest_sequence_ids:
                contest_sequence_ids.add(contest.sequence_order)
            # validate the associated gp unit id
            contests_have_valid_electoral_district_id = contests_have_valid_electoral_district_id \
                and contest.electoral_district_id in gp_unit_ids
            # validate the number elected (seats)
            contests_have_valid_number_elected = contests_have_valid_number_elected \
                and contest.number_elected < len(contest.ballot_selections)
            # validate the number of votes per voter
            contests_have_valid_number_votes_allowed = contests_have_valid_number_votes_allowed \
                and (contest.votes_allowed is None or contest.number_elected <= contest.votes_allowed)
            if type(contest) is CandidateContest:    
                if contest.primary_party_ids is not None:
                    for primary_party_id in contest.primary_party_ids:
                        # validate the party ids
                        candidate_contests_have_valid_party_ids = candidate_contests_have_valid_party_ids \
                            and primary_party_id in party_ids

        contests_valid = len(contest_ids) is len(self.contests) \
            and len(contest_sequence_ids) is len(self.contests) \
            and contests_have_valid_electoral_district_id \
            and contests_have_valid_number_elected \
            and contests_have_valid_number_votes_allowed \
            and candidate_contests_have_valid_party_ids

        # Validate Contest Selections
        contest_selections_have_valid_sequence_ids = True
        contest_selections_have_valid_candidate_ids = True

        selection_count = 0

        for contest in self.contests:
            sequence_ids: Set[int] = set()
            for selection in contest.ballot_selections:
                selection_count += 1
                # validate the object_id
                if selection.object_id not in selection_ids:
                    selection_ids.add(selection.object_id)
                # validate the sequence_order
                if selection.sequence_order not in sequence_ids:
                    sequence_ids.add(selection.sequence_order)
                # validate the candidate id
                contest_selections_have_valid_candidate_ids = contest_selections_have_valid_candidate_ids \
                    and selection.candidate_id in candidate_ids
            contest_selections_have_valid_sequence_ids = contest_selections_have_valid_sequence_ids \
                and len(sequence_ids) is len(contest.ballot_selections)

        selections_valid = len(selection_ids) is selection_count \
            and contest_selections_have_valid_sequence_ids \
            and contest_selections_have_valid_candidate_ids
        
        success = \
            geopolitical_units_valid \
            and ballot_styles_valid \
            and parties_valid \
            and candidates_valid \
            and contests_valid \
            and selections_valid

        if not success:
            log_warning("Election is_valid: %s", str({
                    "geopolitical_units_valid": geopolitical_units_valid,
                    "ballot_styles_valid": ballot_styles_valid,
                    "ballot_styles_have_valid_gp_unit_ids": ballot_styles_have_valid_gp_unit_ids,
                    "parties_valid": parties_valid,
                    "candidates_valid": candidates_valid,
                    "candidates_have_valid_party_ids": candidates_have_valid_party_ids,
                    "contests_valid": contests_valid,
                    "contests_have_valid_electoral_district_id": contests_have_valid_electoral_district_id,
                    "contests_have_valid_number_elected": contests_have_valid_number_elected,
                    "contests_have_valid_number_votes_allowed": contests_have_valid_number_votes_allowed,
                    "candidate_contests_have_valid_party_ids": candidate_contests_have_valid_party_ids,
                    "selections_valid": selections_valid,
                    "contest_selections_have_valid_sequence_ids": contest_selections_have_valid_sequence_ids,
                    "contest_selections_have_valid_candidate_ids": contest_selections_have_valid_candidate_ids
                    }))
        return success
