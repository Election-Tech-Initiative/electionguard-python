import unittest
from copy import deepcopy
from datetime import timedelta
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings

from electionguard.encrypt import (
    encrypt_contest,
    encrypt_selection,
    EncryptionCompositor
)

from electionguard.decrypt import (
    decrypt_selection_with_secret,
    decrypt_selection_with_nonce,
    decrypt_contest_with_secret,
    decrypt_contest_with_nonce,
    decrypt_ballot_with_nonce,
    decrypt_ballot_with_secret
)

from electionguard.election import (
    ContestDescription,
    SelectionDescription
)

from electionguard.elgamal import (
    ElGamalKeyPair
)

from electionguard.group import (
    ElementModQ,
    TWO_MOD_P,
    mult_p,
)

from electionguardtest.elgamal import arb_elgamal_keypair
from electionguardtest.group import arb_element_mod_q_no_zero

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()

class TestDecrypt(unittest.TestCase):

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
    def test_decrypt_selection_valid_input_succeeds(self,
        selection_description: Tuple[str, SelectionDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = selection_description
        data = ballot_factory.get_random_selection_from(description)

        # Act
        subject = encrypt_selection(data, description, keypair.public_key, seed)
        result_from_key = decrypt_selection_with_secret(subject, description, keypair.public_key, keypair.secret_key)
        result_from_nonce = decrypt_selection_with_nonce(subject, description, keypair.public_key)
        result_from_nonce_seed = decrypt_selection_with_nonce(subject, description, keypair.public_key, seed)

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)
        self.assertEqual(data.plaintext, result_from_key.plaintext)
        self.assertEqual(data.plaintext, result_from_nonce.plaintext)
        self.assertEqual(data.plaintext, result_from_nonce_seed.plaintext)

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
    def test_decrypt_selection_valid_input_tampered_fails(self,
        selection_description: Tuple[str, SelectionDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = selection_description
        data = ballot_factory.get_random_selection_from(description)

        # Act
        subject = encrypt_selection(data, description, keypair.public_key, seed)

        # tamper with the encryption
        malformed_encryption = deepcopy(subject)
        malformed_message = malformed_encryption.message._replace(
            alpha=mult_p(subject.message.alpha, TWO_MOD_P)
        )
        malformed_encryption.message = malformed_message

        # tamper with the proof
        malformed_proof = deepcopy(subject)
        malformed_disjunctive = malformed_proof.proof._replace(
            a0=mult_p(subject.proof.a0, TWO_MOD_P)
        )
        malformed_proof.proof = malformed_disjunctive


        result_from_key_malformed_encryption = decrypt_selection_with_secret(
            malformed_encryption, description, keypair.public_key, keypair.secret_key
        )

        result_from_key_malformed_proof = decrypt_selection_with_secret(
            malformed_proof, description, keypair.public_key, keypair.secret_key
        )

        result_from_nonce_malformed_encryption = decrypt_selection_with_nonce(
            malformed_encryption, description, keypair.public_key
        )
        result_from_nonce_malformed_proof = decrypt_selection_with_nonce(
            malformed_proof, description, keypair.public_key
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
    )
    @given(
        ElectionFactory.get_contest_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_decrypt_contest_valid_input_succeeds(self,
        contest_description: Tuple[str, ContestDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = contest_description
        data = ballot_factory.get_random_contest_from(description)

        # Act
        subject = encrypt_contest(data, description, keypair.public_key, seed)
        result_from_key = decrypt_contest_with_secret(subject, description, keypair.public_key, keypair.secret_key)
        result_from_nonce = decrypt_contest_with_nonce(subject, description, keypair.public_key)
        result_from_nonce_seed = decrypt_contest_with_nonce(subject, description, keypair.public_key, seed)

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)

        # The decrypted contest should include an entry for each possible selection
        # and placeholders for each seat
        expected_entries = len(description.ballot_selections) + description.number_elected
        self.assertTrue(
            result_from_key.is_valid(
                description.object_id, expected_entries, description.number_elected, description.votes_allowed
            ))
        self.assertTrue(
            result_from_nonce.is_valid(
                description.object_id, expected_entries, description.number_elected, description.votes_allowed
            ))
        self.assertTrue(
            result_from_nonce_seed.is_valid(
                description.object_id, expected_entries, description.number_elected, description.votes_allowed
            ))

        # Assert the ballot selections sum to the expected number of selections
        key_selected = sum([selection.to_int() for selection in result_from_key.ballot_selections])
        nonce_selected = sum([selection.to_int() for selection in result_from_nonce.ballot_selections])
        seed_selected = sum([selection.to_int() for selection in result_from_nonce_seed.ballot_selections])

        self.assertEqual(key_selected, nonce_selected)
        self.assertEqual(seed_selected, nonce_selected)
        self.assertEqual(description.number_elected, key_selected)

        # Assert each selection is valid
        for selection_description in description.ballot_selections:
            
            key_selection = [selection for selection in result_from_key.ballot_selections if selection.object_id == selection_description.object_id][0]
            nonce_selection = [selection for selection in result_from_nonce.ballot_selections if selection.object_id == selection_description.object_id][0]
            seed_selection = [selection for selection in result_from_nonce_seed.ballot_selections if selection.object_id == selection_description.object_id][0]

            data_selections_exist = [selection for selection in data.ballot_selections if selection.object_id == selection_description.object_id]

            # It's possible there are no selections in the original data collection
            # since it is valid to pass in a ballot that is not complete
            if any(data_selections_exist):
                self.assertTrue(data_selections_exist[0].to_int() == key_selection.to_int())
                self.assertTrue(data_selections_exist[0].to_int() == nonce_selection.to_int())
                self.assertTrue(data_selections_exist[0].to_int() == seed_selection.to_int())
            
            # TODO: also check edge cases such as:
            # - placeholder selections are true for under votes

            self.assertTrue(key_selection.is_valid(selection_description.object_id))
            self.assertTrue(nonce_selection.is_valid(selection_description.object_id))
            self.assertTrue(seed_selection.is_valid(selection_description.object_id))

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
    )
    @given(
        arb_elgamal_keypair()
    )
    def test_decrypt_ballot_valid_input_succeeds(self, keypair: ElGamalKeyPair):
        """
        Check that decryption works as expected by encrypting a ballot using the stateful `EncryptionCompositor`
        and then calling the various decrypt functions.
        """

        # TODO: Hypothesis test instead

        # Arrange
        election = election_factory.get_simple_election_from_file()
        metadata, encryption_context = election_factory.get_fake_cyphertext_election(election, keypair.public_key)

        data = ballot_factory.get_simple_ballot_from_file()
        operator = EncryptionCompositor(metadata, encryption_context)

        # Act
        subject = operator.encrypt(data)
        result_from_key = decrypt_ballot_with_secret(
            subject, metadata, encryption_context.crypto_extended_base_hash, keypair.public_key, keypair.secret_key
        )
        result_from_nonce = decrypt_ballot_with_nonce(
            subject, metadata, encryption_context.crypto_extended_base_hash, keypair.public_key
        )
        result_from_nonce_seed = decrypt_ballot_with_nonce(
            subject, metadata, encryption_context.crypto_extended_base_hash, keypair.public_key, subject.nonce
        )

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertIsNotNone(result_from_nonce_seed)
        self.assertEqual(data.object_id, subject.object_id)
        self.assertEqual(data.object_id, result_from_key.object_id)
        self.assertEqual(data.object_id, result_from_nonce.object_id)
        self.assertEqual(data.object_id, result_from_nonce_seed.object_id)

        for description in metadata.get_contests_for(data.ballot_style):

            expected_entries = len(description.ballot_selections) + description.number_elected

            key_contest = [contest for contest in result_from_key.contests if contest.object_id == description.object_id][0]
            nonce_contest = [contest for contest in result_from_nonce.contests if contest.object_id == description.object_id][0]
            seed_contest = [contest for contest in result_from_nonce_seed.contests if contest.object_id == description.object_id][0]

            # Contests may not be voted on the ballot
            data_contest_exists = [contest for contest in data.contests if contest.object_id == description.object_id]
            if any(data_contest_exists):
                data_contest = data_contest_exists[0]
            else:
                data_contest = None

            self.assertTrue(
                key_contest.is_valid(
                    description.object_id, expected_entries, description.number_elected, description.votes_allowed
                ))
            self.assertTrue(
                nonce_contest.is_valid(
                    description.object_id, expected_entries, description.number_elected, description.votes_allowed
                ))
            self.assertTrue(
                seed_contest.is_valid(
                    description.object_id, expected_entries, description.number_elected, description.votes_allowed
                ))

            for selection_description in description.ballot_selections:
                
                key_selection = [selection for selection in key_contest.ballot_selections if selection.object_id == selection_description.object_id][0]
                nonce_selection = [selection for selection in nonce_contest.ballot_selections if selection.object_id == selection_description.object_id][0]
                seed_selection = [selection for selection in seed_contest.ballot_selections if selection.object_id == selection_description.object_id][0]
                
                # Selections may be undervoted for a specific contest
                if any(data_contest_exists):
                    data_selection_exists = [selection for selection in data_contest.ballot_selections if selection.object_id == selection_description.object_id]
                else:
                    data_selection_exists = []

                if any(data_selection_exists):
                    data_selection = data_selection_exists[0]
                    self.assertTrue(data_selection.to_int() == key_selection.to_int())
                    self.assertTrue(data_selection.to_int() == nonce_selection.to_int())
                    self.assertTrue(data_selection.to_int() == seed_selection.to_int())
                else:
                    data_selection = None

                # TODO: also check edge cases such as:
                # - placeholder selections are true for under votes

                self.assertTrue(key_selection.is_valid(selection_description.object_id))
                self.assertTrue(nonce_selection.is_valid(selection_description.object_id))
                self.assertTrue(seed_selection.is_valid(selection_description.object_id))
