# pylint: disable=protected-access
# pylint: disable=too-many-instance-attributes
# pylint: disable=unnecessary-comprehension

from typing import Dict, List, Tuple
from unittest import TestCase

from electionguard.ballot_box import BallotBox, BallotBoxState, get_ballots
from electionguard.data_store import DataStore
from electionguard.decrypt_with_shares import (
    ELECTION_PUBLIC_KEY,
    decrypt_ballots,
    decrypt_selection_with_decryption_shares,
    decrypt_ballot,
)
from electionguard.decryption import (
    compute_decryption_share,
    compute_decryption_share_for_ballot,
    compute_decryption_share_for_ballots,
    compute_decryption_share_for_selection,
    compute_compensated_decryption_share_for_ballot,
    compute_compensated_decryption_share_for_selection,
    compute_lagrange_coefficients_for_guardians,
    reconstruct_decryption_share_for_ballot,
)
from electionguard.decryption_share import (
    DecryptionShare,
    create_ciphertext_decryption_selection,
)
from electionguard.election_polynomial import compute_lagrange_coefficient
from electionguard.group import (
    mult_p,
    pow_p,
)
from electionguard.election_builder import ElectionBuilder
from electionguard.encrypt import EncryptionMediator
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.tally import tally_ballots
from electionguard.types import GUARDIAN_ID
from electionguard.utils import get_optional

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory
from electionguardtest.identity_encrypt import identity_auxiliary_decrypt
from electionguardtest.key_ceremony_helper import KeyCeremonyHelper
from electionguardtest.tally import accumulate_plaintext_ballots

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestDecryption(TestCase):
    """Test decryption methods"""

    NUMBER_OF_GUARDIANS = 3
    QUORUM = 2
    CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)

    def setUp(self):

        # Key Ceremony
        self.key_ceremony_mediator = KeyCeremonyMediator(
            "key_ceremony_mediator_mediator", self.CEREMONY_DETAILS
        )
        self.guardians: List[Guardian] = KeyCeremonyHelper.create_guardians(
            self.CEREMONY_DETAILS
        )
        KeyCeremonyHelper.perform_full_ceremony(
            self.guardians, self.key_ceremony_mediator
        )
        self.joint_public_key = self.key_ceremony_mediator.publish_joint_key()

        # Setup the election
        manifest = election_factory.get_fake_manifest()
        builder = ElectionBuilder(self.NUMBER_OF_GUARDIANS, self.QUORUM, manifest)
        builder.set_public_key(self.joint_public_key.joint_public_key)
        builder.set_commitment_hash(self.joint_public_key.commitment_hash)
        self.internal_manifest, self.context = get_optional(builder.build())

        self.encryption_device = election_factory.get_encryption_device()
        self.ballot_marking_device = EncryptionMediator(
            self.internal_manifest, self.context, self.encryption_device
        )

        # get some fake ballots
        self.fake_cast_ballot = ballot_factory.get_fake_ballot(
            self.internal_manifest, "some-unique-ballot-id-cast"
        )
        self.more_fake_ballots = []
        for i in range(10):
            self.more_fake_ballots.append(
                ballot_factory.get_fake_ballot(
                    self.internal_manifest, f"some-unique-ballot-id-cast{i}"
                )
            )
        self.fake_spoiled_ballot = ballot_factory.get_fake_ballot(
            self.internal_manifest, "some-unique-ballot-id-spoiled"
        )
        self.more_fake_spoiled_ballots = []
        for i in range(2):
            self.more_fake_spoiled_ballots.append(
                ballot_factory.get_fake_ballot(
                    self.internal_manifest, f"some-unique-ballot-id-spoiled{i}"
                )
            )
        self.assertTrue(
            self.fake_cast_ballot.is_valid(
                self.internal_manifest.ballot_styles[0].object_id
            )
        )
        self.assertTrue(
            self.fake_spoiled_ballot.is_valid(
                self.internal_manifest.ballot_styles[0].object_id
            )
        )
        self.expected_plaintext_tally = accumulate_plaintext_ballots(
            [self.fake_cast_ballot] + self.more_fake_ballots
        )

        # Fill in the expected values with any missing selections
        # that were not made on any ballots
        selection_ids = {
            selection.object_id
            for contest in self.internal_manifest.contests
            for selection in contest.ballot_selections
        }

        missing_selection_ids = selection_ids.difference(
            set(self.expected_plaintext_tally)
        )

        for id in missing_selection_ids:
            self.expected_plaintext_tally[id] = 0

        # Encrypt
        self.encrypted_fake_cast_ballot = self.ballot_marking_device.encrypt(
            self.fake_cast_ballot
        )
        self.encrypted_fake_spoiled_ballot = self.ballot_marking_device.encrypt(
            self.fake_spoiled_ballot
        )

        # encrypt some more fake ballots
        self.more_fake_encrypted_ballots = []
        for fake_ballot in self.more_fake_ballots:
            self.more_fake_encrypted_ballots.append(
                self.ballot_marking_device.encrypt(fake_ballot)
            )
        # encrypt some more fake ballots
        self.more_fake_encrypted_spoiled_ballots = []
        for fake_ballot in self.more_fake_spoiled_ballots:
            self.more_fake_encrypted_spoiled_ballots.append(
                self.ballot_marking_device.encrypt(fake_ballot)
            )

        # configure the ballot box
        ballot_store = DataStore()
        ballot_box = BallotBox(self.internal_manifest, self.context, ballot_store)
        ballot_box.cast(self.encrypted_fake_cast_ballot)
        ballot_box.spoil(self.encrypted_fake_spoiled_ballot)

        # Cast some more fake ballots
        for fake_ballot in self.more_fake_encrypted_ballots:
            ballot_box.cast(fake_ballot)
        # Spoil some more fake ballots
        for fake_ballot in self.more_fake_encrypted_spoiled_ballots:
            ballot_box.spoil(fake_ballot)

        # generate encrypted tally
        self.ciphertext_tally = tally_ballots(
            ballot_store, self.internal_manifest, self.context
        )
        self.ciphertext_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)

    def tearDown(self):
        self.key_ceremony_mediator.reset(
            CeremonyDetails(self.NUMBER_OF_GUARDIANS, self.QUORUM)
        )

    def test_compute_selection(self):
        # Arrange
        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # act
        result = compute_decryption_share_for_selection(
            self.guardians[0]._election_keys, first_selection, self.context
        )

        # assert
        self.assertIsNotNone(result)

    def test_compute_compensated_selection_failure(self):
        # Arrange
        available_guardian = self.guardians[0]
        missing_guardian = self.guardians[2]

        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # Act
        # Get backup for missing guardian instead of one sent by guardian
        incorrect_backup = available_guardian.share_election_partial_key_backup(
            missing_guardian.id
        )

        result = compute_compensated_decryption_share_for_selection(
            available_guardian.share_election_public_key(),
            available_guardian._auxiliary_keys,
            missing_guardian.share_election_public_key(),
            incorrect_backup,
            first_selection,
            self.context,
            identity_auxiliary_decrypt,
        )

        # Assert
        self.assertIsNone(result)

    def test_compute_compensated_selection(self):
        """
        demonstrates the complete workflow for computing a comepnsated decryption share
        For one selection. It is useful for verifying that the workflow is correct
        """
        # Arrange
        available_guardian_1 = self.guardians[0]
        available_guardian_2 = self.guardians[1]
        missing_guardian = self.guardians[2]

        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # Compute lagrange coefficients for the guardians that are present
        lagrange_0 = compute_lagrange_coefficient(
            available_guardian_1.sequence_order,
            *[available_guardian_2.sequence_order],
        )
        lagrange_1 = compute_lagrange_coefficient(
            available_guardian_2.sequence_order,
            *[available_guardian_1.sequence_order],
        )

        print(
            (
                f"lagrange: sequence_orders: ({available_guardian_1.sequence_order}, "
                f"{available_guardian_2.sequence_order}, {missing_guardian.sequence_order})\n"
            )
        )

        print(lagrange_0)
        print(lagrange_1)

        # compute their shares
        share_0 = compute_decryption_share_for_selection(
            available_guardian_1._election_keys, first_selection, self.context
        )

        share_1 = compute_decryption_share_for_selection(
            available_guardian_2._election_keys, first_selection, self.context
        )

        self.assertIsNotNone(share_0)
        self.assertIsNotNone(share_1)

        # compute compensations shares for the missing guardian
        compensation_0 = compute_compensated_decryption_share_for_selection(
            available_guardian_1.share_election_public_key(),
            available_guardian_1._auxiliary_keys,
            missing_guardian.share_election_public_key(),
            missing_guardian.share_election_partial_key_backup(available_guardian_1.id),
            first_selection,
            self.context,
            identity_auxiliary_decrypt,
        )

        compensation_1 = compute_compensated_decryption_share_for_selection(
            available_guardian_2.share_election_public_key(),
            available_guardian_2._auxiliary_keys,
            missing_guardian.share_election_public_key(),
            missing_guardian.share_election_partial_key_backup(available_guardian_2.id),
            first_selection,
            self.context,
            identity_auxiliary_decrypt,
        )

        self.assertIsNotNone(compensation_0)
        self.assertIsNotNone(compensation_1)

        print("\nSHARES:")
        print(compensation_0)
        print(compensation_1)

        # Check the share proofs
        self.assertTrue(
            compensation_0.proof.is_valid(
                first_selection.ciphertext,
                get_optional(
                    available_guardian_1.recovery_public_key_for(missing_guardian.id)
                ),
                compensation_0.share,
                self.context.crypto_extended_base_hash,
            )
        )

        self.assertTrue(
            compensation_1.proof.is_valid(
                first_selection.ciphertext,
                get_optional(
                    available_guardian_2.recovery_public_key_for(missing_guardian.id)
                ),
                compensation_1.share,
                self.context.crypto_extended_base_hash,
            )
        )

        share_pow_p = [
            pow_p(compensation_0.share, lagrange_0),
            pow_p(compensation_1.share, lagrange_1),
        ]

        print("\nSHARE_POW_P")
        print(share_pow_p)

        # reconstruct the missing share from the compensation shares
        reconstructed_share = mult_p(
            *[
                pow_p(compensation_0.share, lagrange_0),
                pow_p(compensation_1.share, lagrange_1),
            ]
        )

        print("\nRECONSTRUCTED SHARE\n")
        print(reconstructed_share)

        share_2 = create_ciphertext_decryption_selection(
            first_selection.object_id,
            missing_guardian.id,
            reconstructed_share,
            {
                available_guardian_1.id: compensation_0,
                available_guardian_2.id: compensation_1,
            },
        )

        # Decrypt the result
        result = decrypt_selection_with_decryption_shares(
            first_selection,
            {
                available_guardian_1.id: (
                    available_guardian_1.share_election_public_key().key,
                    share_0,
                ),
                available_guardian_2.id: (
                    available_guardian_2.share_election_public_key().key,
                    share_1,
                ),
                missing_guardian.id: (
                    missing_guardian.share_election_public_key().key,
                    share_2,
                ),
            },
            self.context.crypto_extended_base_hash,
        )

        print(result)

        self.assertIsNotNone(result)
        self.assertEqual(
            result.tally, self.expected_plaintext_tally[first_selection.object_id]
        )

    def test_decrypt_selection_all_present(self):
        # Arrange
        available_guardians = self.guardians

        # find the first selection
        first_contest = list(self.ciphertext_tally.contests.values())[0]
        first_selection = list(first_contest.selections.values())[0]

        print(first_contest.object_id)
        print(first_selection.object_id)

        # precompute decryption shares for specific selection for the guardians
        shares: Dict[GUARDIAN_ID, Tuple[ELECTION_PUBLIC_KEY, DecryptionShare]] = {
            guardian.id: (
                guardian.share_election_public_key().key,
                compute_decryption_share(
                    guardian._election_keys,
                    self.ciphertext_tally,
                    self.context,
                )
                .contests[first_contest.object_id]
                .selections[first_selection.object_id],
            )
            for guardian in available_guardians
        }

        # Act
        result = decrypt_selection_with_decryption_shares(
            first_selection, shares, self.context.crypto_extended_base_hash
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(
            self.expected_plaintext_tally[first_selection.object_id], result.tally
        )

    def test_decrypt_ballot_all_guardians_present(self):
        # Arrange
        # precompute decryption shares for the guardians
        available_guardians = self.guardians
        plaintext_ballot = self.fake_cast_ballot
        encrypted_ballot = self.encrypted_fake_cast_ballot
        shares = {
            available_guardian.id: compute_decryption_share_for_ballot(
                available_guardian._election_keys,
                encrypted_ballot,
                self.context,
            )
            for available_guardian in available_guardians
        }

        # act
        result = decrypt_ballot(
            encrypted_ballot,
            shares,
            self.context.crypto_extended_base_hash,
        )

        # assert
        self.assertIsNotNone(result)

        for contest in plaintext_ballot.contests:
            for selection in contest.ballot_selections:
                expected_tally = selection.vote
                actual_tally = (
                    result.contests[contest.object_id]
                    .selections[selection.object_id]
                    .tally
                )
                self.assertEqual(expected_tally, actual_tally)

    def test_decrypt_ballots_all_guardians_present(self):
        # Arrange
        # precompute decryption shares for the guardians
        available_guardians = self.guardians
        shares = {
            guardian.id: compute_decryption_share_for_ballots(
                guardian._election_keys,
                list(self.ciphertext_ballots.values()),
                self.context,
            )
            for guardian in available_guardians
        }

        # Act
        result = decrypt_ballots(
            self.ciphertext_ballots,
            shares,
            self.context.crypto_extended_base_hash,
        )

        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(self.fake_spoiled_ballot.object_id in result)

        spoiled_ballot = result[self.fake_spoiled_ballot.object_id]
        for contest in self.fake_spoiled_ballot.contests:
            for selection in contest.ballot_selections:
                self.assertEqual(
                    spoiled_ballot.contests[contest.object_id]
                    .selections[selection.object_id]
                    .tally,
                    result[self.fake_spoiled_ballot.object_id]
                    .contests[contest.object_id]
                    .selections[selection.object_id]
                    .tally,
                )

    def test_decrypt_ballot_compensate_missing_guardians(self):
        # Arrange
        # precompute decryption shares for the guardians
        plaintext_ballot = self.fake_cast_ballot
        encrypted_ballot = self.encrypted_fake_cast_ballot
        available_guardians = self.guardians[0:2]
        missing_guardian = self.guardians[2]

        available_shares = {
            available_guardian.id: compute_decryption_share_for_ballot(
                available_guardian._election_keys,
                encrypted_ballot,
                self.context,
            )
            for available_guardian in available_guardians
        }

        compensated_shares = {
            available_guardian.id: compute_compensated_decryption_share_for_ballot(
                available_guardian.share_election_public_key(),
                available_guardian._auxiliary_keys,
                missing_guardian.share_election_public_key(),
                get_optional(
                    available_guardian._guardian_election_partial_key_backups.get(
                        missing_guardian.id
                    )
                ),
                encrypted_ballot,
                self.context,
                identity_auxiliary_decrypt,
            )
            for available_guardian in available_guardians
        }

        lagrange_coefficients = compute_lagrange_coefficients_for_guardians(
            [guardian.share_election_public_key() for guardian in available_guardians]
        )

        reconstructed_share = reconstruct_decryption_share_for_ballot(
            missing_guardian.share_election_public_key(),
            encrypted_ballot,
            compensated_shares,
            lagrange_coefficients,
        )

        all_shares = {**available_shares, missing_guardian.id: reconstructed_share}

        # act
        result = decrypt_ballot(
            encrypted_ballot,
            all_shares,
            self.context.crypto_extended_base_hash,
        )

        # assert
        self.assertIsNotNone(result)

        for contest in plaintext_ballot.contests:
            for selection in contest.ballot_selections:
                expected_tally = selection.vote
                actual_tally = (
                    result.contests[contest.object_id]
                    .selections[selection.object_id]
                    .tally
                )
                self.assertEqual(expected_tally, actual_tally)
