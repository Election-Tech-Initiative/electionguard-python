import unittest
from datetime import datetime

from electionguard.encryption_compositor import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from
)

from electionguard.ballot import (
    Ballot,
    BallotContest,
    BallotSelection
)

from electionguard.election import (
    BallotStyle,
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

from secrets import randbelow

class TestEncryptionCompositor(unittest.TestCase):

    def get_fake_election(self) -> Election:
        """
        Election(election_scope_id: str, 
        type: ElectionType, start_date: datetime, end_date: datetime, 
        geopolitical_units: List[GeopoliticalUnit], parties: List[Party], 
        candidates: List[Candidate], contests: List[DerivedContestType], ballot_styles: List[BallotStyle]
        """

        fake_ballot_style = BallotStyle("some-ballot-style-id")
        fake_ballot_style.geopolitical_unit_ids = [
            "some-geopoltical-unit-id"
        ]

        fake_referendum_contest = ContestDescription(
            "some-referendum-contest-object-id", "some-geopoltical-unit-id", 0, VoteVariationType.one_of_m, 1)
        fake_referendum_contest.ballot_selections = [
            # Referendum selections are simply a special case of `candidate` in the object model
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-1", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-2", 1),
        ]
        fake_referendum_contest.votes_allowed = 1

        fake_candidate_contest = ContestDescription(
            "some-candidate-contest-object-id", "some-geopoltical-unit-id", 1, VoteVariationType.one_of_m, 2)
        fake_candidate_contest.ballot_selections = [
            SelectionDescription("some-object-id-candidate-1", "some-candidate-id-1", 0),
            SelectionDescription("some-object-id-candidate-2", "some-candidate-id-2", 1),
            SelectionDescription("some-object-id-candidate-3", "some-candidate-id-3", 2)
        ]
        fake_candidate_contest.votes_allowed = 2

        fake_election = Election(
            election_scope_id = "some-scope-id",
            type = ElectionType.unknown,
            start_date = datetime.now(),
            end_date = datetime.now(),
            geopolitical_units = [
                GeopoliticalUnit("some-geopoltical-unit-id", "some-gp-unit-name", ReportingUnitType.unknown)
            ],
            parties = [
                Party("some-party-id-1"),
                Party("some-party-id-2")
            ],
            candidates = [
                Candidate("some-candidate-id-1"),
                Candidate("some-candidate-id-2"),
                Candidate("some-candidate-id-3"),
            ],
            contests = [
                fake_referendum_contest,
                fake_candidate_contest
            ],
            ballot_styles = [
                fake_ballot_style
            ]
        )

        return fake_election

    def get_fake_ballot(self) -> Ballot:

        fake_election = self.get_fake_election()
        
        fake_ballot = Ballot(
            "some-unique-ballot-id-123", 
            fake_election.ballot_styles[0].object_id, 
            [
                contest_from(fake_election.contests[0]),
                contest_from(fake_election.contests[1])
            ])

        return fake_ballot

    def test_encrypt_selection_succeeds(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription("some-selection-object-id", "some-candidate-id", 1)
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        result = encrypt_selection(subject, metadata, keypair.public_key, nonce)

        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    # def test_decrypt_selection_succeeds(self):
    #     pass

    def test_encrypt_contest_referendum_succeeds(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = ContestDescription("some-contest-object-id", "some-electoral-district-id", 0, VoteVariationType.one_of_m, 1)
        metadata.ballot_selections = [
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-affirmative", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-negative", 1),
        ]
        metadata.votes_allowed = 1
        hash_context = metadata.crypto_hash()

        subject = contest_from(metadata)
        result = encrypt_contest(subject, metadata, keypair.public_key, nonce)

        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    def test_encrypt_ballot_simple_succeeds(self):
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        metadata = self.get_fake_election()
        hash_context = metadata.crypto_extended_hash(keypair.public_key)

        subject = self.get_fake_ballot()
        result = encrypt_ballot(subject, metadata, keypair.public_key)

        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

