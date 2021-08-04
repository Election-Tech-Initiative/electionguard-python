from copy import deepcopy
from datetime import timedelta
from random import Random
from typing import Tuple

from hypothesis import HealthCheck, Phase
from hypothesis import given, settings
from hypothesis.strategies import integers

from tests.base_test_case import BaseTestCase

from electionguard.chaum_pedersen import DisjunctiveChaumPedersenProof
from electionguard.decrypt_with_secrets import (
    decrypt_selection_with_secret,
    decrypt_selection_with_nonce,
    decrypt_contest_with_secret,
    decrypt_contest_with_nonce,
    decrypt_ballot_with_nonce,
    decrypt_ballot_with_secret,
)
from electionguard.elgamal import ElGamalKeyPair, ElGamalCiphertext
from electionguard.encrypt import (
    encrypt_contest,
    encrypt_selection,
    EncryptionMediator,
)
from electionguard.group import (
    ElementModQ,
    TWO_MOD_P,
    ONE_MOD_Q,
    mult_p,
    int_to_q_unchecked,
)
from electionguard.manifest import (
    ContestDescription,
    SelectionDescription,
    generate_placeholder_selections_from,
    contest_description_with_placeholders_from,
)

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory
from electionguardtest.elgamal import elgamal_keypairs
from electionguardtest.group import elements_mod_q_no_zero


election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestDecryptWithSecrets(BaseTestCase):
    """Decrypting with secrets tests"""

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_decrypt_selection_valid_input_succeeds(
        self,
        selection_description: Tuple[str, SelectionDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        random = Random(random_seed)
        _, description = selection_description
        data = ballot_factory.get_random_selection_from(description, random)

        # Act
        subject = encrypt_selection(
            data, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )
        self.assertIsNotNone(subject)

        result_from_key = decrypt_selection_with_secret(
            subject, description, keypair.public_key, keypair.secret_key, ONE_MOD_Q
        )
        result_from_nonce = decrypt_selection_with_nonce(
            subject, description, keypair.public_key, ONE_MOD_Q
        )
        result_from_nonce_seed = decrypt_selection_with_nonce(
            subject, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)
        self.assertEqual(data.vote, result_from_key.vote)
        self.assertEqual(data.vote, result_from_nonce.vote)
        self.assertEqual(data.vote, result_from_nonce_seed.vote)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_decrypt_selection_valid_input_tampered_fails(
        self,
        selection_description: Tuple[str, SelectionDescription],
        keypair: ElGamalKeyPair,
        seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = selection_description
        random = Random(random_seed)
        data = ballot_factory.get_random_selection_from(description, random)

        # Act
        subject = encrypt_selection(
            data, description, keypair.public_key, ONE_MOD_Q, seed
        )

        # tamper with the encryption
        malformed_encryption = deepcopy(subject)
        malformed_message = malformed_encryption.ciphertext._replace(
            pad=mult_p(subject.ciphertext.pad, TWO_MOD_P)
        )
        malformed_encryption.ciphertext = malformed_message

        # tamper with the proof
        malformed_proof = deepcopy(subject)
        altered_a0 = mult_p(subject.proof.proof_zero_pad, TWO_MOD_P)
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

        result_from_key_malformed_encryption = decrypt_selection_with_secret(
            malformed_encryption,
            description,
            keypair.public_key,
            keypair.secret_key,
            ONE_MOD_Q,
        )

        result_from_key_malformed_proof = decrypt_selection_with_secret(
            malformed_proof,
            description,
            keypair.public_key,
            keypair.secret_key,
            ONE_MOD_Q,
        )

        result_from_nonce_malformed_encryption = decrypt_selection_with_nonce(
            malformed_encryption, description, keypair.public_key, ONE_MOD_Q
        )
        result_from_nonce_malformed_proof = decrypt_selection_with_nonce(
            malformed_proof, description, keypair.public_key, ONE_MOD_Q
        )

        # Assert
        self.assertIsNone(result_from_key_malformed_encryption)
        self.assertIsNone(result_from_key_malformed_proof)
        self.assertIsNone(result_from_nonce_malformed_encryption)
        self.assertIsNone(result_from_nonce_malformed_proof)

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_decrypt_selection_tampered_nonce_fails(
        self,
        selection_description: Tuple[str, SelectionDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        random = Random(random_seed)
        _, description = selection_description
        data = ballot_factory.get_random_selection_from(description, random)

        # Act
        subject = encrypt_selection(
            data, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )
        self.assertIsNotNone(subject)

        # Tamper with the nonce by setting it to an arbitrary value
        subject.nonce = nonce_seed

        result_from_nonce_seed = decrypt_selection_with_nonce(
            subject, description, keypair.public_key, ONE_MOD_Q, nonce_seed
        )

        # Assert
        self.assertIsNone(result_from_nonce_seed)

    @settings(
        deadline=timedelta(milliseconds=5000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_decrypt_contest_valid_input_succeeds(
        self,
        contest_description: Tuple[str, ContestDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = contest_description
        random = Random(random_seed)
        data = ballot_factory.get_random_contest_from(description, random)

        placeholders = generate_placeholder_selections_from(
            description, description.number_elected
        )
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )

        self.assertTrue(description_with_placeholders.is_valid())

        # Act
        subject = encrypt_contest(
            data,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
        )
        self.assertIsNotNone(subject)

        # Decrypt the contest, but keep the placeholders
        # so we can verify the selection count matches as expected in the test
        result_from_key = decrypt_contest_with_secret(
            subject,
            description_with_placeholders,
            keypair.public_key,
            keypair.secret_key,
            ONE_MOD_Q,
            remove_placeholders=False,
        )
        result_from_nonce = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            remove_placeholders=False,
        )
        result_from_nonce_seed = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
            remove_placeholders=False,
        )

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)

        # The decrypted contest should include an entry for each possible selection
        # and placeholders for each seat
        expected_entries = (
            len(description.ballot_selections) + description.number_elected
        )
        self.assertTrue(
            result_from_key.is_valid(
                description.object_id,
                expected_entries,
                description.number_elected,
                description.votes_allowed,
            )
        )
        self.assertTrue(
            result_from_nonce.is_valid(
                description.object_id,
                expected_entries,
                description.number_elected,
                description.votes_allowed,
            )
        )
        self.assertTrue(
            result_from_nonce_seed.is_valid(
                description.object_id,
                expected_entries,
                description.number_elected,
                description.votes_allowed,
            )
        )

        # Assert the ballot selections sum to the expected number of selections
        key_selected = sum(
            [selection.vote for selection in result_from_key.ballot_selections]
        )
        nonce_selected = sum(
            [selection.vote for selection in result_from_nonce.ballot_selections]
        )
        seed_selected = sum(
            [selection.vote for selection in result_from_nonce_seed.ballot_selections]
        )

        self.assertEqual(key_selected, nonce_selected)
        self.assertEqual(seed_selected, nonce_selected)
        self.assertEqual(description.number_elected, key_selected)

        # Assert each selection is valid
        for selection_description in description.ballot_selections:

            key_selection = [
                selection
                for selection in result_from_key.ballot_selections
                if selection.object_id == selection_description.object_id
            ][0]
            nonce_selection = [
                selection
                for selection in result_from_nonce.ballot_selections
                if selection.object_id == selection_description.object_id
            ][0]
            seed_selection = [
                selection
                for selection in result_from_nonce_seed.ballot_selections
                if selection.object_id == selection_description.object_id
            ][0]

            data_selections_exist = [
                selection
                for selection in data.ballot_selections
                if selection.object_id == selection_description.object_id
            ]

            # It's possible there are no selections in the original data collection
            # since it is valid to pass in a ballot that is not complete
            if any(data_selections_exist):
                self.assertTrue(data_selections_exist[0].vote == key_selection.vote)
                self.assertTrue(data_selections_exist[0].vote == nonce_selection.vote)
                self.assertTrue(data_selections_exist[0].vote == seed_selection.vote)

            # TODO: also check edge cases such as:
            # - placeholder selections are true for under votes

            self.assertTrue(key_selection.is_valid(selection_description.object_id))
            self.assertTrue(nonce_selection.is_valid(selection_description.object_id))
            self.assertTrue(seed_selection.is_valid(selection_description.object_id))

    @settings(
        deadline=timedelta(milliseconds=5000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        elgamal_keypairs(),
        elements_mod_q_no_zero(),
        integers(),
    )
    def test_decrypt_contest_invalid_input_fails(
        self,
        contest_description: Tuple[str, ContestDescription],
        keypair: ElGamalKeyPair,
        nonce_seed: ElementModQ,
        random_seed: int,
    ):

        # Arrange
        _, description = contest_description
        random = Random(random_seed)
        data = ballot_factory.get_random_contest_from(description, random)

        placeholders = generate_placeholder_selections_from(
            description, description.number_elected
        )
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )

        self.assertTrue(description_with_placeholders.is_valid())

        # Act
        subject = encrypt_contest(
            data,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
        )
        self.assertIsNotNone(subject)

        # tamper with the nonce
        subject.nonce = int_to_q_unchecked(1)

        result_from_nonce = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            remove_placeholders=False,
        )
        result_from_nonce_seed = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
            remove_placeholders=False,
        )

        # Assert
        self.assertIsNone(result_from_nonce)
        self.assertIsNone(result_from_nonce_seed)

        # Tamper with the encryption
        subject.ballot_selections[0].ciphertext = ElGamalCiphertext(
            TWO_MOD_P, TWO_MOD_P
        )

        result_from_key_tampered = decrypt_contest_with_secret(
            subject,
            description_with_placeholders,
            keypair.public_key,
            keypair.secret_key,
            ONE_MOD_Q,
            remove_placeholders=False,
        )
        result_from_nonce_tampered = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            remove_placeholders=False,
        )
        result_from_nonce_seed_tampered = decrypt_contest_with_nonce(
            subject,
            description_with_placeholders,
            keypair.public_key,
            ONE_MOD_Q,
            nonce_seed,
            remove_placeholders=False,
        )

        # Assert
        self.assertIsNone(result_from_key_tampered)
        self.assertIsNone(result_from_nonce_tampered)
        self.assertIsNone(result_from_nonce_seed_tampered)

    @settings(
        deadline=timedelta(milliseconds=5000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(elgamal_keypairs())
    def test_decrypt_ballot_valid_input_succeeds(self, keypair: ElGamalKeyPair):
        """
        Check that decryption works as expected by encrypting a ballot using the stateful `EncryptionMediator`
        and then calling the various decrypt functions.
        """

        # TODO: Hypothesis test instead

        # Arrange
        election = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        device = election_factory.get_encryption_device()
        operator = EncryptionMediator(internal_manifest, context, device)

        # Act
        subject = operator.encrypt(data)
        self.assertIsNotNone(subject)

        result_from_key = decrypt_ballot_with_secret(
            subject,
            internal_manifest,
            context.crypto_extended_base_hash,
            keypair.public_key,
            keypair.secret_key,
            remove_placeholders=False,
        )
        result_from_nonce = decrypt_ballot_with_nonce(
            subject,
            internal_manifest,
            context.crypto_extended_base_hash,
            keypair.public_key,
            remove_placeholders=False,
        )
        result_from_nonce_seed = decrypt_ballot_with_nonce(
            subject,
            internal_manifest,
            context.crypto_extended_base_hash,
            keypair.public_key,
            subject.nonce,
            remove_placeholders=False,
        )

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)
        self.assertEqual(data.object_id, subject.object_id)
        self.assertEqual(data.object_id, result_from_key.object_id)
        self.assertEqual(data.object_id, result_from_nonce.object_id)
        self.assertEqual(data.object_id, result_from_nonce_seed.object_id)

        for description in internal_manifest.get_contests_for(data.style_id):

            expected_entries = (
                len(description.ballot_selections) + description.number_elected
            )

            key_contest = [
                contest
                for contest in result_from_key.contests
                if contest.object_id == description.object_id
            ][0]
            nonce_contest = [
                contest
                for contest in result_from_nonce.contests
                if contest.object_id == description.object_id
            ][0]
            seed_contest = [
                contest
                for contest in result_from_nonce_seed.contests
                if contest.object_id == description.object_id
            ][0]

            # Contests may not be voted on the ballot
            data_contest_exists = [
                contest
                for contest in data.contests
                if contest.object_id == description.object_id
            ]
            if any(data_contest_exists):
                data_contest = data_contest_exists[0]
            else:
                data_contest = None

            self.assertTrue(
                key_contest.is_valid(
                    description.object_id,
                    expected_entries,
                    description.number_elected,
                    description.votes_allowed,
                )
            )
            self.assertTrue(
                nonce_contest.is_valid(
                    description.object_id,
                    expected_entries,
                    description.number_elected,
                    description.votes_allowed,
                )
            )
            self.assertTrue(
                seed_contest.is_valid(
                    description.object_id,
                    expected_entries,
                    description.number_elected,
                    description.votes_allowed,
                )
            )

            for selection_description in description.ballot_selections:

                key_selection = [
                    selection
                    for selection in key_contest.ballot_selections
                    if selection.object_id == selection_description.object_id
                ][0]
                nonce_selection = [
                    selection
                    for selection in nonce_contest.ballot_selections
                    if selection.object_id == selection_description.object_id
                ][0]
                seed_selection = [
                    selection
                    for selection in seed_contest.ballot_selections
                    if selection.object_id == selection_description.object_id
                ][0]

                # Selections may be undervoted for a specific contest
                if any(data_contest_exists):
                    data_selection_exists = [
                        selection
                        for selection in data_contest.ballot_selections
                        if selection.object_id == selection_description.object_id
                    ]
                else:
                    data_selection_exists = []

                if any(data_selection_exists):
                    data_selection = data_selection_exists[0]
                    self.assertTrue(data_selection.vote == key_selection.vote)
                    self.assertTrue(data_selection.vote == nonce_selection.vote)
                    self.assertTrue(data_selection.vote == seed_selection.vote)
                else:
                    data_selection = None

                # TODO: also check edge cases such as:
                # - placeholder selections are true for under votes

                self.assertTrue(key_selection.is_valid(selection_description.object_id))
                self.assertTrue(
                    nonce_selection.is_valid(selection_description.object_id)
                )
                self.assertTrue(
                    seed_selection.is_valid(selection_description.object_id)
                )

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(elgamal_keypairs())
    def test_decrypt_ballot_valid_input_missing_nonce_fails(
        self, keypair: ElGamalKeyPair
    ):

        # Arrange
        election = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        device = election_factory.get_encryption_device()
        operator = EncryptionMediator(internal_manifest, context, device)

        # Act
        subject = operator.encrypt(data)
        self.assertIsNotNone(subject)
        subject.nonce = None

        missing_nonce_value = None

        result_from_nonce = decrypt_ballot_with_nonce(
            subject,
            internal_manifest,
            context.crypto_extended_base_hash,
            keypair.public_key,
        )

        # SUGGEST this test is the same as the one above
        result_from_nonce_seed = decrypt_ballot_with_nonce(
            subject,
            internal_manifest,
            context.crypto_extended_base_hash,
            keypair.public_key,
            missing_nonce_value,
        )

        # Assert
        self.assertIsNone(result_from_nonce)
        self.assertIsNone(result_from_nonce_seed)
