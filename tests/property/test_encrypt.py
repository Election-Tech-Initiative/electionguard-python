from unittest import skip
from unittest.mock import patch
from copy import deepcopy
from datetime import timedelta
from random import Random
from secrets import randbelow
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers


from tests.base_test_case import BaseTestCase

import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard_tools.strategies.elgamal import elgamal_keypairs
from electionguard_tools.strategies.group import elements_mod_q_no_zero

from electionguard.constants import get_small_prime
from electionguard.chaum_pedersen import (
    ConstantChaumPedersenProof,
    DisjunctiveChaumPedersenProof,
    make_constant_chaum_pedersen,
    make_disjunctive_chaum_pedersen,
)
from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
    elgamal_add,
)
from electionguard.encrypt import (
    EncryptionDevice,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from,
    EncryptionMediator,
)
from electionguard.group import (
    ElementModQ,
    ONE_MOD_Q,
    TWO_MOD_Q,
    int_to_q,
    add_q,
    TWO_MOD_P,
    mult_p,
)
from electionguard.manifest import (
    ContestDescription,
    contest_description_with_placeholders_from,
    generate_placeholder_selections_from,
    SelectionDescription,
    VoteVariationType,
)


election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()
SEED = election_factory.get_encryption_device().get_hash()


class TestEncrypt(BaseTestCase):
    """Encryption tests"""

    def test_encrypt_simple_selection_succeeds(self):

        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        nonce = randbelow(get_small_prime())
        metadata = SelectionDescription(
            "some-selection-object-id", 1, "some-candidate-id"
        )
        hash_context = metadata.crypto_hash()

        subject = selection_from(metadata)
        self.assertTrue(subject.is_valid(metadata.object_id))

        # Act
        result = encrypt_selection(
            subject,
            metadata,
            keypair.public_key,
            ONE_MOD_Q,
            nonce,
            should_verify_proofs=True,
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
        nonce = randbelow(get_small_prime())
        metadata = SelectionDescription(
            "some-selection-object-id", 1, "some-candidate-id"
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
            subject,
            description,
            keypair.public_key,
            ONE_MOD_Q,
            seed,
            should_verify_proofs=True,
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
        malformed_encryption.ciphertext.pad = mult_p(result.ciphertext.pad, TWO_MOD_P)

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
        contest_description: Tuple[str, ContestDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _id, description = contest_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_contest_from(description, random)

        # Act
        result = encrypt_contest(
            subject,
            description,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
            should_verify_proofs=True,
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
        contest_description: Tuple[str, ContestDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _id, description = contest_description
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

    @skip("runs forever")
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
        contest_description: Tuple[str, ContestDescription],
        keypair: ElGamalKeyPair,
        seed: ElementModQ,
        overvotes: int,
        random_seed: int,
    ):
        # Arrange
        _id, description = contest_description
        random = Random(random_seed)
        subject = ballot_factory.get_random_contest_from(description, random)

        for _i in range(overvotes):
            overvote = ballot_factory.get_random_selection_from(
                description.ballot_selections[0], random
            )
            subject.ballot_selections.append(overvote)

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
                    "0@A.com-selection",
                    0,
                    "0@A.com",
                ),
                SelectionDescription("0@B.com-selection", 1, "0@B.com"),
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
                    "0@A.com-selection",
                    0,
                    "0@A.com",
                ),
                # Note the selection description is the same as the first sequence element
                SelectionDescription(
                    "0@A.com-selection",
                    1,
                    "0@A.com",
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
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )
        nonce_seed = TWO_MOD_Q

        # TODO: Ballot Factory
        subject = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(subject.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act
        result = encrypt_ballot(subject, internal_manifest, context, SEED)
        result_from_seed = encrypt_ballot(
            subject,
            internal_manifest,
            context,
            SEED,
            nonce_seed,
            should_verify_proofs=True,
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.code)
        self.assertIsNotNone(result_from_seed)
        self.assertTrue(
            result.is_valid_encryption(
                internal_manifest.manifest_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )
        self.assertTrue(
            result_from_seed.is_valid_encryption(
                internal_manifest.manifest_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    def test_encrypt_ballot_with_composer_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_fake_manifest()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )

        data = election_factory.get_fake_ballot(internal_manifest)
        self.assertTrue(data.is_valid(internal_manifest.ballot_styles[0].object_id))

        device = election_factory.get_encryption_device()
        subject = EncryptionMediator(internal_manifest, context, device)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(
            result.is_valid_encryption(
                internal_manifest.manifest_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    def test_encrypt_simple_ballot_from_file_with_composer_succeeds(self):
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(internal_manifest.ballot_styles[0].object_id))

        device = EncryptionDevice(12345, 23456, 34567, "Location")
        subject = EncryptionMediator(internal_manifest, context, device)

        # Act
        result = subject.encrypt(data)

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(data.object_id, result.object_id)
        self.assertTrue(
            result.is_valid_encryption(
                internal_manifest.manifest_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

    def test_encrypt_simple_ballot_from_files_succeeds(self) -> None:
        # Arrange
        keypair = elgamal_keypair_from_secret(int_to_q(2))
        manifest = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )

        device = EncryptionDevice(12345, 23456, 34567, "Location")
        ballot = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(ballot.is_valid(internal_manifest.ballot_styles[0].object_id))

        # Act

        ciphertext = encrypt_ballot(
            ballot,
            internal_manifest,
            context,
            device.get_hash(),
            TWO_MOD_Q,
            should_verify_proofs=True,
        )

        # Assert
        self.assertIsNotNone(ciphertext)
        self.assertEqual(ballot.object_id, ciphertext.object_id)
        self.assertTrue(
            ciphertext.is_valid_encryption(
                internal_manifest.manifest_hash,
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
        manifest = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        self.assertTrue(data.is_valid(internal_manifest.ballot_styles[0].object_id))

        device = election_factory.get_encryption_device()
        subject = EncryptionMediator(internal_manifest, context, device)

        # Act
        result = subject.encrypt(data)
        self.assertTrue(
            result.is_valid_encryption(
                internal_manifest.manifest_hash,
                keypair.public_key,
                context.crypto_extended_base_hash,
            )
        )

        # Assert
        for contest in result.contests:
            # Find the contest description
            contest_description = list(
                filter(
                    lambda i, c=contest: i.object_id == c.object_id,
                    internal_manifest.contests,
                )
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

    def test_encrypt_ballot_with_verify_proofs_false_passed_on(self):
        """
        This test is for https://github.com/microsoft/electionguard-python/issues/459
        """
        with patch("electionguard.encrypt.encrypt_contest") as patched_contest, patch(
            "electionguard.encrypt.encrypt_selection"
        ) as patched_selection:
            # Arrange
            keypair = elgamal_keypair_from_secret(int_to_q(2))
            manifest = election_factory.get_fake_manifest()
            internal_manifest, context = election_factory.get_fake_ciphertext_election(
                manifest, keypair.public_key
            )
            subject = election_factory.get_fake_ballot(internal_manifest)
            self.assertTrue(
                subject.is_valid(internal_manifest.ballot_styles[0].object_id)
            )

            patched_contest.side_effect = encrypt_contest
            patched_selection.side_effect = encrypt_selection

            # Act
            encrypt_ballot(
                subject, internal_manifest, context, SEED, should_verify_proofs=False
            )

            # Assert
            for call in patched_contest.call_args_list:
                self.assertFalse(call.kwargs.get("should_verify_proofs"))
            for call in patched_selection.call_args_list:
                self.assertFalse(call.kwargs.get("should_verify_proofs"))
