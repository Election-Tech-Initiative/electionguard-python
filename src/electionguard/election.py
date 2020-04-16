from dataclasses import dataclass, field
from enum import Enum, unique
from datetime import datetime, timezone
from typing import Optional, List, TypeVar, Generic, Set, Union, Iterable

from .group import ElementModQ, ElementModP
from .logs import log_warning

from .is_valid import IsValid
from .serializable import Serializable
from .hash import CryptoHashable, hashable_element, flatten, hash_elems

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
class AnnotatedString(Serializable, CryptoHashable):
    """
    """
    annotation: str = field(default="")
    value: str = field(default="")

    def crypto_hash(self) -> ElementModQ:
        """
        """
        return hash_elems(self.annotation, self.value)

@dataclass
class Language(Serializable, CryptoHashable):
    """
    Internationalized Text
    """
    value: str
    language: str = field(default="en")

    def crypto_hash(self) -> ElementModQ:
        """
        """
        return hash_elems(self.value, self.language)

@dataclass
class InternationalizedText(Serializable, CryptoHashable):
    """
    """
    text: List[Language] = field(default_factory=lambda: [])

    def crypto_hash(self) -> ElementModQ:
        """
        """
        text_hashes = [
            t.crypto_hash() for t in self.text
        ]
        return hash_elems(*text_hashes)

@dataclass
class ContactInformation(Serializable, CryptoHashable):
    """
    """
    address_line: Optional[List[str]] = field(default=None)
    email: Optional[List[AnnotatedString]] = field(default=None)
    phone: Optional[List[AnnotatedString]] = field(default=None)
    name: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        """

        return hash_elems(*flatten(
            self.name,
            self.address_line,
            self.email,
            self.phone
        ))

@dataclass
class GeopoliticalUnit(Serializable, CryptoHashable):
    """
    """
    object_id: str
    name: str
    type: ReportingUnitType
    contact_information: Optional[ContactInformation] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        """
        return hash_elems(*flatten(
            self.object_id, 
            self.name, 
            str(self.type), 
            self.contact_information
            )
        )

@dataclass
class BallotStyle(Serializable, CryptoHashable):
    """
    """
    object_id: str
    geopolitical_unit_ids: Optional[List[str]] = field(default=None)
    party_ids: Optional[List[str]] = field(default=None)
    image_uri: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        """
        return hash_elems(*flatten(
            self.object_id,
            self.geopolitical_unit_ids,
            self.party_ids,
            self.image_uri
            )
        )

@dataclass
class Party(Serializable, CryptoHashable):
    """
    """
    object_id: str
    ballot_name: InternationalizedText = field(default=InternationalizedText())
    abbreviation: Optional[str] = field(default=None)
    color: Optional[str] = field(default=None)
    logo_uri: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        """

        return hash_elems(*flatten(
            self.object_id, 
            self.ballot_name.crypto_hash(), 
            self.abbreviation, 
            self.color, 
            self.logo_uri
            )
        )

@dataclass
class Candidate(Serializable, CryptoHashable):
    """
    Candidate
    """
    object_id: str
    ballot_name: InternationalizedText = field(default=InternationalizedText())
    party_id: Optional[str] = field(default=None)
    image_uri: Optional[str] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        """

        return hash_elems(*flatten(
            self.object_id, 
            self.ballot_name.crypto_hash(), 
            self.party_id, 
            self.image_uri
            )
        )

@dataclass
class Selection(Serializable):
    """
    typed selection object
    """
    object_id: str

@dataclass
class SelectionDescription(Selection, CryptoHashable):
    candidate_id: str
    sequence_order: int

    def crypto_hash(self) -> ElementModQ:
        """
        """

        return hash_elems(
            self.object_id, 
            str(self.sequence_order), 
            self.candidate_id
        )

@dataclass
class Contest(Serializable):
    object_id: str

@dataclass
class ContestDescription(Contest, CryptoHashable):
    """
    """
    electoral_district_id: str
    sequence_order: int
    vote_variation: VoteVariationType

    """
    The number of candidate seats 
    """
    number_elected: int
    ballot_selections: List[SelectionDescription] = field(default_factory=lambda: [])
    ballot_title: Optional[InternationalizedText] = field(default=None)
    ballot_subtitle: Optional[InternationalizedText] = field(default=None)
    # TODO: not optional
    name: Optional[str] = field(default=None)
    # TODO: not optional
    
    
    """
    Indicates the number of individual votes a voter has.
    If no value is present, assumed to be number elected
    """
    votes_allowed: Optional[int] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        Given a ContestDescription, deterministically derives a "hash" of that contest,
        suitable for use in ElectionGuard's "base hash" values, and for validating that
        either a plaintext or encrypted voted context and its corresponding contest
        description match up.
        """

        return hash_elems(*flatten(
            self.object_id, 
            str(self.sequence_order),
            self.electoral_district_id, 
            str(self.vote_variation), 
            self.ballot_title,
            self.ballot_subtitle,
            self.name,
            str(self.number_elected),
            str(self.votes_allowed),
            self.ballot_selections
            )
        )

@dataclass
class CandidateContestDescription(ContestDescription):
    """
    """
    primary_party_ids: List[str] = field(default_factory=lambda: [])

@dataclass
class ReferendumContestDescription(ContestDescription):
    """
    """
    pass

DerivedContestType = Union[CandidateContestDescription, ReferendumContestDescription]

@dataclass
class Election(Serializable, IsValid, CryptoHashable):
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

    crypto_base_hash: Optional[str] = field(default=None)
    crypto_extended_base_hash: Optional[str] = field(default=None)
    elgamal_public_key: Optional[ElementModP] = field(default=None)

    def crypto_hash(self) -> ElementModQ:
        """
        Returns a hash of the description components of the election
        """

        if self.crypto_base_hash is not None:
            return self.crypto_base_hash

        gp_unit_hashes = [
            gpunit.crypto_hash() for gpunit in self.geopolitical_units
        ]
        party_hashes = [
            party.crypto_hash() for party in self.parties
        ]
        candidate_hashes = [
            candidate.crypto_hash() for candidate in self.parties
        ]
        contest_hashes = [
            contest.crypto_hash() for contest in self.contests
        ]
        ballot_style_hashes = [
            ballot_style.crypto_hash() for ballot_style in self.ballot_styles
        ]

        self.crypto_base_hash = hash_elems(*flatten(
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
            self.ballot_styles
            )
        )

        return self.crypto_base_hash
        
    def crypto_extended_hash(self, elgamal_public_key: ElementModP) -> ElementModQ:
        """
        """

        if self.crypto_extended_base_hash is not None:
            return self.crypto_extended_base_hash

        if self.elgamal_public_key is None:
            self.elgamal_public_key = elgamal_public_key

        self.crypto_extended_base_hash = hash_elems(self.crypto_hash(), self.elgamal_public_key)
        return self.crypto_extended_base_hash
        
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
            if type(contest) is CandidateContestDescription:    
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
