import unittest
from copy import deepcopy
from datetime import timedelta
from typing import List, Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers

from electionguard.encryption_compositor import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from,
    EncryptionCompositor
)

from electionguard.ballot import (
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    CyphertextBallotSelection
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

from electionguard.chaum_pedersen import (
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen
)

from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
    elgamal_add,
)
from electionguard.group import (
    ElementModP,
    ElementModQ,
    ONE_MOD_Q,
    TWO_MOD_Q,
    int_to_q,
    add_q,
    flatmap_optional,
    unwrap_optional,
    Q,
    TWO_MOD_P,
    mult_p,
)

from electionguardtest.elgamal import arb_elgamal_keypair
from electionguardtest.group import arb_element_mod_q_no_zero

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

from secrets import randbelow

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()

class TestEncryptionCompositor(unittest.TestCase):

    def test_encrypt_simple_selection_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription("some-selection-object-id", "some-candidate-id", 1)
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        self.assertTrue(subject.is_valid(metadata.object_id))

        # Act
        result = encrypt_selection(subject, metadata, keypair.public_key, nonce)

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.message)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_selection_valid_input_succeeds(
        self,
        selection_description: Tuple[str, SelectionDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = selection_description
        subject = ballot_factory.get_random_selection_from(description)

        # Act
        result = encrypt_selection(subject, description, keypair.public_key, seed)

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.message)
        self.assertTrue(result.is_valid_encryption(description.crypto_hash(), keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_selection_valid_input_tampered_encryption_fails(
        self,
        selection_description: Tuple[str, SelectionDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = selection_description
        subject = ballot_factory.get_random_selection_from(description)

        # Act
        result = encrypt_selection(subject, description, keypair.public_key, seed, should_verify_proofs=False)
        self.assertTrue(result.is_valid_encryption(description.crypto_hash(), keypair.public_key))

        # tamper with the encryption
        malformed_encryption = deepcopy(result)
        malformed_message = malformed_encryption.message._replace(
            alpha=mult_p(result.message.alpha, TWO_MOD_P)
        )
        malformed_encryption.message = malformed_message

        # tamper with the proof
        malformed_proof = deepcopy(result)
        malformed_disjunctive = malformed_proof.proof._replace(
            a0=mult_p(result.proof.a0, TWO_MOD_P)
        )
        malformed_proof.proof = malformed_disjunctive

        # Assert
        self.assertFalse(malformed_encryption.is_valid_encryption(description.crypto_hash(), keypair.public_key))
        self.assertFalse(malformed_proof.is_valid_encryption(description.crypto_hash(), keypair.public_key))

    def test_encrypt_simple_contest_referendum_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = ContestDescription("some-contest-object-id", "some-electoral-district-id", 0, VoteVariationType.one_of_m, 1, 1)
        metadata.ballot_selections = [
            SelectionDescription("some-object-id-affirmative", "some-candidate-id-affirmative", 0),
            SelectionDescription("some-object-id-negative", "some-candidate-id-negative", 1),
        ]
        metadata.votes_allowed = 1
        hash_context = metadata.crypto_hash()

        subject = contest_from(metadata)
        self.assertTrue(subject.is_valid(
            metadata.object_id,
            len(metadata.ballot_selections),
            metadata.number_elected,
            metadata.votes_allowed
        ))

        # Act
        result = encrypt_contest(subject, metadata, keypair.public_key, nonce)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(hash_context, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_contest_valid_input_succeeds(
        self, 
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        seed: ElementModQ):
        
        # Arrange
        _, description = contest_description
        subject = ballot_factory.get_random_contest_from(description)

        # Act
        result = encrypt_contest(subject, description, keypair.public_key, seed)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(description.crypto_hash(), keypair.public_key))

        # The encrypted contest should include an entry for each possible selection
        # and placeholders for each seat
        expected_entries = len(description.ballot_selections) + description.number_elected
        self.assertEqual(len(result.ballot_selections), expected_entries)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_contest_valid_input_tampered_proof_succeeds(
        self, 
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        seed: ElementModQ):
        
        # Arrange
        _, description = contest_description
        subject = ballot_factory.get_random_contest_from(description)

        # Act
        result = encrypt_contest(subject, description, keypair.public_key, seed)
        self.assertTrue(result.is_valid_encryption(description.crypto_hash(), keypair.public_key))

        # tamper with the proof
        malformed_proof = deepcopy(result)
        malformed_disjunctive = malformed_proof.proof._replace(
            a=mult_p(result.proof.a, TWO_MOD_P)
        )
        malformed_proof.proof = malformed_disjunctive

        # Assert
        self.assertFalse(malformed_proof.is_valid_encryption(description.crypto_hash(), keypair.public_key))
        
    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
        integers(1, 6)
    )
    def test_encrypt_contest_overvote_fails(
        self, 
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        seed: ElementModQ, 
        overvotes: int
    ):
        # Arrange
        _, description = contest_description
        subject = ballot_factory.get_random_contest_from(description)

        highest_sequence = max(*[selection.sequence_order for selection in description.ballot_selections], 1)

        for i in range(overvotes):
            extra = ballot_factory.get_random_selection_from(description.ballot_selections[0])
            extra.sequence_order = highest_sequence + i + 1
            subject.ballot_selections.append(extra)

        # Act
        result = encrypt_contest(subject, description, keypair.public_key, seed)

        # Assert
        self.assertIsNone(result)

    def test_encrypt_ballot_simple_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        metadata = election_factory.get_fake_election()
        encryption_context = CyphertextElection(1, 1, metadata.crypto_hash())
        
        encryption_context.set_crypto_context(keypair.public_key)

        subject = election_factory.get_fake_ballot(metadata)
        self.assertTrue(subject.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        result = encrypt_ballot(subject, metadata, encryption_context)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(encryption_context.crypto_extended_base_hash, keypair.public_key))

    def test_encrypt_ballot_valid_input_succeeds(self):
        pass

    def test_encrypt_ballot_with_stateful_composer_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        metadata = election_factory.get_fake_election()
        encryption_context = CyphertextElection(1, 1, metadata.crypto_hash())
        encryption_context.set_crypto_context(keypair.public_key)

        data = election_factory.get_fake_ballot(metadata)
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        subject = EncryptionCompositor(metadata, encryption_context)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(encryption_context.crypto_extended_base_hash, keypair.public_key))

    def test_encrypt_simple_ballot_from_files_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        metadata = election_factory.get_simple_election_from_file()
        encryption_context = CyphertextElection(1, 1, metadata.crypto_hash())
        encryption_context.set_crypto_context(keypair.public_key)

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        subject = EncryptionCompositor(metadata, encryption_context)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result.is_valid_encryption(encryption_context.crypto_extended_base_hash, keypair.public_key))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        arb_elgamal_keypair()
    )
    def test_encrypt_ballot_with_derivative_nonces_regenerates_valid_proofs(self, keypair: ElGamalKeyPair):
        """
        This test verifies that we can regenerate the contest and selection proofs from the cached nonce values
        """

        # TODO: Hypothesis test instead

        # Arrange
        metadata = election_factory.get_simple_election_from_file()
        encryption_context = election_factory.get_fake_cyphertext_election(metadata.crypto_hash(), keypair.public_key)

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        subject = EncryptionCompositor(metadata, encryption_context)

        # Act
        result = subject.encrypt(data)
        self.assertTrue(result.is_valid_encryption(encryption_context.crypto_extended_base_hash, keypair.public_key))

        # Assert
        for contest in result.contests:
            # Find the contest description
            contest_description = list(filter(lambda i: i.object_id == contest.object_id, metadata.contests))[0]

            # Homomorpically accumulate the selection encryptions
            elgamal_accumulation = elgamal_add(*[selection.message for selection in contest.ballot_selections])
            # accumulate the selection nonce's
            aggregate_nonce = add_q(*[selection.nonce for selection in contest.ballot_selections])

            regenerated_constant = make_constant_chaum_pedersen(
                elgamal_accumulation,
                contest_description.number_elected,
                aggregate_nonce,
                keypair.public_key,
                add_q(contest.nonce, TWO_MOD_Q),
            )

            self.assertTrue(regenerated_constant.is_valid(elgamal_accumulation, keypair.public_key))

            for selection in contest.ballot_selections:
                # Since we know the nonce, we can decrypt the plaintext
                representation = selection.message.decrypt_known_nonce(keypair.public_key, selection.nonce)

                # one could also decrypt with the secret key:
                #representation = selection.message.decrypt(keypair.secret_key)

                regenerated_disjuctive = make_disjunctive_chaum_pedersen(
                    selection.message,
                    selection.nonce,
                    keypair.public_key,
                    add_q(selection.nonce, TWO_MOD_Q),
                    representation,
                )

                self.assertTrue(regenerated_disjuctive.is_valid(selection.message, keypair.public_key))

        