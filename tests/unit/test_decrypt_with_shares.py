# pylint: disable=protected-access
# pylint: disable=too-many-instance-attributes
# pylint: disable=unnecessary-comprehension

from typing import Dict, List, Tuple

from tests.base_test_case import BaseTestCase

from electionguard.ballot_box import BallotBox, BallotBoxState, get_ballots
from electionguard.data_store import DataStore
from electionguard.decrypt_with_shares import (
    decrypt_selection_with_decryption_shares,
    decrypt_ballot,
)
from electionguard.decryption import (
    compute_decryption_share,
    compute_decryption_share_for_ballot,
    compute_compensated_decryption_share_for_ballot,
    compute_lagrange_coefficients_for_guardians,
    reconstruct_decryption_share_for_ballot,
)
from electionguard.decryption_share import DecryptionShare
from electionguard.election_builder import ElectionBuilder
from electionguard.encrypt import EncryptionMediator
from electionguard.group import ElementModP
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.tally import tally_ballots
from electionguard.type import GUARDIAN_ID
from electionguard.utils import get_optional

import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard_tools.helpers.identity_encrypt import identity_auxiliary_decrypt
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)
from electionguard_tools.helpers.tally_accumulate import accumulate_plaintext_ballots

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestDecryptWithShares(BaseTestCase):
    """Test decrypt with shares methods"""

    NUMBER_OF_GUARDIANS = 3
    QUORUM = 2
    CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)

    def setUp(self):

        # Key Ceremony
        self.key_ceremony_mediator = KeyCeremonyMediator(
            "key_ceremony_mediator_mediator", self.CEREMONY_DETAILS
        )
        self.guardians: List[Guardian] = KeyCeremonyOrchestrator.create_guardians(
            self.CEREMONY_DETAILS
        )
        KeyCeremonyOrchestrator.perform_full_ceremony(
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

    def test_decrypt_selection_with_all_guardians_present(self):
        # Arrange
        available_guardians = self.guardians

        # find the first selection
        first_contest = list(self.ciphertext_tally.contests.values())[0]
        first_selection = list(first_contest.selections.values())[0]

        print(first_contest.object_id)
        print(first_selection.object_id)

        # precompute decryption shares for specific selection for the guardians
        shares: Dict[GUARDIAN_ID, Tuple[ElementModP, DecryptionShare]] = {
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

    def test_decrypt_ballot_with_all_guardians_present(self):
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

    def test_decrypt_ballot_with_missing_guardians(self):
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
