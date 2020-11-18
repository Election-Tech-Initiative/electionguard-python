import unittest
from copy import deepcopy
from datetime import timedelta
from random import Random
from secrets import randbelow
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory
from electionguard.chaum_pedersen import (
    ConstantChaumPedersenProof,
    DisjunctiveChaumPedersenProof,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
)
from electionguard.election import (
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    contest_description_with_placeholders_from,
    generate_placeholder_selections_from,
    SelectionDescription,
    VoteVariationType,
)
from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
    elgamal_add,
)
from electionguard.encrypt import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from,
    EncryptionDevice,
    EncryptionMediator,
)
from electionguard.group import (
    ElementModQ,
    ONE_MOD_Q,
    TWO_MOD_Q,
    int_to_q,
    add_q,
    Q,
    TWO_MOD_P,
    mult_p,
)
from electionguardtest.elgamal import elgamal_keypairs
from electionguardtest.group import elements_mod_q_no_zero

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()
SEED_HASH = EncryptionDevice("Location").get_hash()


class TestEncrypt(unittest.TestCase):
    def test_encrypt_simple_selection_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription(
            "some-selection-object-id", "some-candidate-id", 1
        )
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        self.assertTrue(subject.is_valid(metadata.object_id))

        # Act
        result = encrypt_selection(
            subject, metadata, keypair.public_key, ONE_MOD_Q, nonce
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.ciphertext)
        self.assertTrue(
            result.is_valid_encryption(hash_context, keypair.public_key, ONE_MOD_Q)
        )

    def test_encrypt_simple_selection_malformed_data_fails(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        metadata = SelectionDescription(
            "some-selection-object-id", "some-candidate-id", 1
        )
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        self.assertTrue(subject.is_valid(metadata.object_id))

        # Act
        result = encrypt_selection(
            subject, metadata, keypair.public_key, ONE_MOD_Q, nonce
        )

        # tamper with the description_hash
        malformed_description_hash = deepcopy(result)
        malformed_description_hash.description_hash = TWO_MOD_Q

        # remove the proof
        missing_proof = deepcopy(result)
        missing_proof.proof = None

        # Assert
        self.assertFalse(
            malformed_description_hash.is_valid_encryption(
                hash_context, keypair.public_key, ONE_MOD_Q
            )
        )
        self.assertFalse(
            missing_proof.is_valid_encryption(
                hash_context, keypair.public_key, ONE_MOD_Q
            )
        )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_encrypt_selection_valid_input_succeeds(
        self,
        selection_description: Tuple[str, SelectionDescription],
        keypair: ElGamalKeyPair,
        seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = selection_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_selection_from(description, random)

        # Act
        result = encrypt_selection(
            subject, description, keypair.public_key, ONE_MOD_Q, seed
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.ciphertext)
        self.assertTrue(
            result.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_encrypt_selection_valid_input_tampered_encryption_fails(
        self,
        selection_description: Tuple[str, SelectionDescription],
        keypair: ElGamalKeyPair,
        seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = selection_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_selection_from(description, random)

        # Act
        result = encrypt_selection(
            subject,
            description,
            keypair.public_key,
            ONE_MOD_Q,
            seed,
            should_verify_proofs=False,
        )
        self.assertTrue(
            result.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

        # tamper with the encryption
        malformed_encryption = deepcopy(result)
        malformed_message = malformed_encryption.ciphertext._replace(
            pad=mult_p(result.ciphertext.pad, TWO_MOD_P)
        )
        malformed_encryption.ciphertext = malformed_message

        # tamper with the proof
        malformed_proof = deepcopy(result)
        altered_a0 = mult_p(result.proof.proof_zero_pad, TWO_MOD_P)
        malformed_disjunctive = DisjunctiveChaumPedersenProof(
            altered_a0,
            malformed_proof.proof.proof_zero_data,
            malformed_proof.proof.proof_one_pad,
            malformed_proof.proof.proof_one_data,
            malformed_proof.proof.proof_zero_challenge,
            malformed_proof.proof.proof_one_challenge,
            malformed_proof.proof.challenge,
            malformed_proof.proof.proof_zero_response,
            malformed_proof.proof.proof_one_response,
        )
        malformed_proof.proof = malformed_disjunctive

        # Assert
        self.assertFalse(
            malformed_encryption.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )
        self.assertFalse(
            malformed_proof.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

    def test_encrypt_simple_contest_referendum_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(Q)
        ballot_selections = [
            SelectionDescription(
                "some-object-id-affirmative", "some-candidate-id-affirmative", 0
            ),
            SelectionDescription(
                "some-object-id-negative", "some-candidate-id-negative", 1
            ),
        ]
        placeholder_selections = [
            SelectionDescription(
                "some-object-id-placeholder", "some-candidate-id-placeholder", 2
            )
        ]
        metadata = ContestDescriptionWithPlaceholders(
            "some-contest-object-id",
            "some-electoral-district-id",
            0,
            VoteVariationType.one_of_m,
            1,
            1,
            "some-referendum-contest-name",
            ballot_selections,
            None,
            None,
            placeholder_selections,
        )
        hash_context = metadata.crypto_hash()

        subject = contest_from(metadata)
        self.assertTrue(
            subject.is_valid(
                metadata.object_id,
                len(metadata.ballot_selections),
                metadata.number_elected,
                metadata.votes_allowed,
            )
        )

        # Act
        result = encrypt_contest(
            subject, metadata, keypair.public_key, ONE_MOD_Q, nonce
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(
            result.is_valid_encryption(hash_context, keypair.public_key, ONE_MOD_Q)
        )

    @settings(
        deadline=timedelta(milliseconds=4000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_encrypt_contest_valid_input_succeeds(
        self,
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = contest_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_contest_from(description, random)

        # Act
        result = encrypt_contest(
            subject, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(
            result.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

        # The encrypted contest should include an entry for each possible selection
        # and placeholders for each seat
        expected_entries = (
            len(description.ballot_selections) + description.number_elected
        )
        self.assertEqual(len(result.ballot_selections), expected_entries)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_encrypt_contest_valid_input_tampered_proof_fails(
        self,
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = contest_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_contest_from(description, random)

        # Act
        result = encrypt_contest(
            subject, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )
        self.assertTrue(
            result.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

        # tamper with the proof
        malformed_proof = deepcopy(result)
        altered_a = mult_p(result.proof.pad, TWO_MOD_P)
        malformed_disjunctive = ConstantChaumPedersenProof(
            altered_a,
            malformed_proof.proof.data,
            malformed_proof.proof.challenge,
            malformed_proof.proof.response,
            malformed_proof.proof.constant,
        )
        malformed_proof.proof = malformed_disjunctive

        # remove the proof
        missing_proof = deepcopy(result)
        missing_proof.proof = None

        # Assert
        self.assertFalse(
            malformed_proof.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )
        self.assertFalse(
            missing_proof.is_valid_encryption(
                description.crypto_hash(), keypair.public_key, ONE_MOD_Q
            )
        )

    @unittest.skip("runs forever")
    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(1, 6),
        integers(),
    )
    def test_encrypt_contest_overvote_fails(
        self,
        contest_description: ContestDescription,
        keypair: ElGamalKeyPair,
        seed: ElementModQ,
        overvotes: int,
        random_seed: int,
    ):
        # Arrange
        _, description = contest_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_contest_from(description, random)

        highest_sequence = max(
            *[selection.sequence_order for selection in description.ballot_selections],
            1,
        )

        for i in range(overvotes):
            extra = ballot_factory.get_random_selection_from(
                description.ballot_selections[0], random
            )
            extra.sequence_order = highest_sequence + i + 1
            subject.ballot_selections.append(extra)

        # Act
        result = encrypt_contest(
            subject, description, keypair.public_key, ONE_MOD_Q, seed
        )

        # Assert
        self.assertIsNone(result)

    def test_encrypt_contest_manually_formed_contest_description_valid_succeeds(self):
        description = ContestDescription(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=0,
                ),
                SelectionDescription(
                    object_id="0@B.com-selection",
                    candidate_id="0@B.com",
                    sequence_order=1,
                ),
            ],
            ballot_title=None,
            ballot_subtitle=None,
        )

        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        seed = ONE_MOD_Q

        ####################
        data = ballot_factory.get_random_contest_from(description, Random(0))

        placeholders = generate_placeholder_selections_from(
            description, description.number_elected
        )
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )

        # Act
        subject = encrypt_contest(
            data,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            seed,
            should_verify_proofs=True,
        )
        self.assertIsNotNone(subject)

    def test_encrypt_contest_duplicate_selection_object_ids_fails(self):
        """
        This is an example test of a failing test where the contest description
        is malformed
        """
        random_seed = 0

        description = ContestDescription(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=0,
                ),
                # Note the selection description is the same as the first sequence element
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=1,
                ),
            ],
        )

        keypair = elgamal_keypair_from_secret(TWO_MOD_Q)
        seed = ONE_MOD_Q

        # Bypass checking the validity of the description
        data = ballot_factory.get_random_contest_from(
            description, Random(0), suppress_validity_check=True
        )

        placeholders = generate_placeholder_selections_from(
            description, description.number_elected
        )
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )

        # Act
        subject = encrypt_contest(
            data, description_with_placeholders, keypair.public_key, ONE_MOD_Q, seed
        )
        self.assertIsNone(subject)

    def test_encrypt_ballot_simple_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )
        nonce_seed = TWO_MOD_Q

        # TODO: Ballot Factory
        subject = election_factory.get_fake_ballot(metadata)
        self.assertTrue(subject.is_valid(metadata.ballot_styles[0].object_id))

        # Act
        result = encrypt_ballot(subject, metadata, context, SEED_HASH)
        tracker_code = result.get_tracker_code()
        result_from_seed = encrypt_ballot(
            subject, metadata, context, SEED_HASH, nonce_seed
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.tracking_hash)
        self.assertIsNotNone(tracker_code)
        self.assertIsNotNone(result_from_seed)
        self.assertTrue(
            result.is_valid_encryption(
                metadata.description_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )
        self.assertTrue(
            result_from_seed.is_valid_encryption(
                metadata.description_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    def test_encrypt_ballot_with_stateful_composer_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_fake_election()
        metadata, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        data = election_factory.get_fake_ballot(metadata)
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        device = EncryptionDevice("Location")
        subject = EncryptionMediator(metadata, context, device)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(
            result.is_valid_encryption(
                metadata.description_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    def test_encrypt_simple_ballot_from_files_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        election = election_factory.get_simple_election_from_file()
        metadata, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        device = EncryptionDevice("Location")
        subject = EncryptionMediator(metadata, context, device)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(data.object_id, result.object_id)
        self.assertTrue(
            result.is_valid_encryption(
                metadata.description_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    @settings(
        deadline=timedelta(milliseconds=4000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elgamal_keypairs())
    def test_encrypt_ballot_with_derivative_nonces_regenerates_valid_proofs(
        self, keypair: ElGamalKeyPair
    ):
        """
        This test verifies that we can regenerate the contest and selection proofs from the cached nonce values
        """

        # TODO: Hypothesis test instead

        # Arrange
        election = election_factory.get_simple_election_from_file()
        metadata, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(metadata.ballot_styles[0].object_id))

        device = EncryptionDevice("Location")
        subject = EncryptionMediator(metadata, context, device)

        # Act
        result = subject.encrypt(data)
        self.assertTrue(
            result.is_valid_encryption(
                metadata.description_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

        # Assert
        for contest in result.contests:
            # Find the contest description
            contest_description = list(
                filter(lambda i: i.object_id == contest.object_id, metadata.contests)
            )[0]

            # Homomorpically accumulate the selection encryptions
            elgamal_accumulation = elgamal_add(
                *[selection.ciphertext for selection in contest.ballot_selections]
            )
            # accumulate the selection nonce's
            aggregate_nonce = add_q(
                *[selection.nonce for selection in contest.ballot_selections]
            )

            regenerated_constant = make_constant_chaum_pedersen(
                elgamal_accumulation,
                contest_description.number_elected,
                aggregate_nonce,
                keypair.public_key,
                add_q(contest.nonce, TWO_MOD_Q),
                context.crypto_extended_base_hash,
            )

            self.assertTrue(
                regenerated_constant.is_valid(
                    elgamal_accumulation,
                    keypair.public_key,
                    context.crypto_extended_base_hash,
                )
            )

            for selection in contest.ballot_selections:
                # Since we know the nonce, we can decrypt the plaintext
                representation = selection.ciphertext.decrypt_known_nonce(
                    keypair.public_key, selection.nonce
                )

                # one could also decrypt with the secret key:
                # representation = selection.message.decrypt(keypair.secret_key)

                regenerated_disjuctive = make_disjunctive_chaum_pedersen(
                    selection.ciphertext,
                    selection.nonce,
                    keypair.public_key,
                    context.crypto_extended_base_hash,
                    add_q(selection.nonce, TWO_MOD_Q),
                    representation,
                )

                self.assertTrue(
                    regenerated_disjuctive.is_valid(
                        selection.ciphertext,
                        keypair.public_key,
                        context.crypto_extended_base_hash,
                    )
                )
