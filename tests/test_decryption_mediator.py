from unittest import TestCase
from datetime import timedelta
from typing import Dict, List
from random import randrange

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers, data

from electionguard.ballot import PlaintextBallot, from_ciphertext_ballot
from electionguard.ballot_box import get_ballots
from electionguard.data_store import DataStore

from electionguard.ballot_box import BallotBox, BallotBoxState
from electionguard.decrypt_with_shares import (
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
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.decryption_share import create_ciphertext_decryption_selection
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.election_polynomial import compute_lagrange_coefficient
from electionguard.encrypt import (
    EncryptionDevice,
    EncryptionMediator,
    encrypt_ballot,
    generate_device_uuid,
)
from electionguard.group import (
    int_to_q_unchecked,
    mult_p,
    pow_p,
)
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.manifest import InternalManifest
from electionguard.tally import (
    CiphertextTally,
    PlaintextTally,
    tally_ballots,
)
from electionguard.utils import get_optional

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

from electionguardtest.election import election_descriptions, plaintext_voted_ballots

from electionguardtest.tally import accumulate_plaintext_ballots

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()
identity_auxiliary_decrypt = lambda message, public_key: message
identity_auxiliary_encrypt = lambda message, private_key: message


class TestDecryptionMediator(TestCase):
    """Test suite for DecryptionMediator"""

    NUMBER_OF_GUARDIANS = 3
    QUORUM = 2
    CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)

    def setUp(self):

        self.key_ceremony = KeyCeremonyMediator(self.CEREMONY_DETAILS)

        self.guardians: List[Guardian] = []

        # Setup Guardians
        for i in range(self.NUMBER_OF_GUARDIANS):
            sequence = i + 2
            self.guardians.append(
                Guardian(
                    "guardian_" + str(sequence),
                    sequence,
                    self.NUMBER_OF_GUARDIANS,
                    self.QUORUM,
                )
            )

        # Attendance (Public Key Share)
        for guardian in self.guardians:
            self.key_ceremony.announce(guardian)

        self.key_ceremony.orchestrate(identity_auxiliary_encrypt)
        self.key_ceremony.verify(identity_auxiliary_decrypt)

        self.joint_public_key = self.key_ceremony.publish_joint_key()
        self.assertIsNotNone(self.joint_public_key)

        # setup the election
        manifest = election_factory.get_fake_manifest()
        builder = ElectionBuilder(self.NUMBER_OF_GUARDIANS, self.QUORUM, manifest)

        self.assertIsNone(builder.build())  # Can't build without the public key

        builder.set_public_key(self.joint_public_key.joint_public_key)
        builder.set_commitment_hash(self.joint_public_key.commitment_hash)
        self.internal_manifest, self.context = get_optional(builder.build())

        self.encryption_device = EncryptionDevice(
            generate_device_uuid(), "Session", 12345, "Location"
        )
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
        self.assertIsNotNone(self.encrypted_fake_cast_ballot)
        self.assertIsNotNone(self.encrypted_fake_spoiled_ballot)
        self.assertTrue(
            self.encrypted_fake_cast_ballot.is_valid_encryption(
                self.internal_manifest.manifest_hash,
                self.joint_public_key.joint_public_key,
                self.context.crypto_extended_base_hash,
            )
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
        self.key_ceremony.reset(CeremonyDetails(self.NUMBER_OF_GUARDIANS, self.QUORUM))

    def test_announce(self):
        # Arrange
        subject = DecryptionMediator(
            self.context,
            self.ciphertext_tally,
            self.ciphertext_ballots,
        )

        # act
        result = subject.announce(self.guardians[0])

        # assert
        self.assertIsNotNone(result)

        # Can only announce once
        self.assertIsNotNone(subject.announce(self.guardians[0]))

        subject.announce(self.guardians[1])

        # Cannot get plaintext tally or spoiled ballots without a quorum
        self.assertIsNone(subject.get_plaintext_tally())
        self.assertIsNone(subject.get_plaintext_ballots())

    def test_compute_selection(self):
        # Arrange
        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # act
        result = compute_decryption_share_for_selection(
            self.guardians[0], first_selection, self.context
        )

        # assert
        self.assertIsNotNone(result)

    def test_compute_compensated_selection_failure(self):
        # Arrange
        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # Act
        self.guardians[0]._guardian_election_partial_key_backups.pop(
            self.guardians[2].object_id
        )

        self.assertIsNone(
            self.guardians[0].recovery_public_key_for(self.guardians[2].object_id)
        )

        result = compute_compensated_decryption_share_for_selection(
            self.guardians[0],
            self.guardians[2].object_id,
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
        first_selection = [
            selection
            for contest in self.ciphertext_tally.contests.values()
            for selection in contest.selections.values()
        ][0]

        # Compute lagrange coefficients for the guardians that are present
        lagrange_0 = compute_lagrange_coefficient(
            self.guardians[0].sequence_order,
            *[self.guardians[1].sequence_order],
        )
        lagrange_1 = compute_lagrange_coefficient(
            self.guardians[1].sequence_order,
            *[self.guardians[0].sequence_order],
        )

        print(
            (
                f"lagrange: sequence_orders: ({self.guardians[0].sequence_order}, "
                f"{self.guardians[1].sequence_order}, {self.guardians[2].sequence_order})\n"
            )
        )

        print(lagrange_0)
        print(lagrange_1)

        # compute their shares
        share_0 = compute_decryption_share_for_selection(
            self.guardians[0], first_selection, self.context
        )

        share_1 = compute_decryption_share_for_selection(
            self.guardians[1], first_selection, self.context
        )

        self.assertIsNotNone(share_0)
        self.assertIsNotNone(share_1)

        # compute compensations shares for the missing guardian
        compensation_0 = compute_compensated_decryption_share_for_selection(
            self.guardians[0],
            self.guardians[2].object_id,
            first_selection,
            self.context,
            identity_auxiliary_decrypt,
        )

        compensation_1 = compute_compensated_decryption_share_for_selection(
            self.guardians[1],
            self.guardians[2].object_id,
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
                    self.guardians[0].recovery_public_key_for(
                        self.guardians[2].object_id
                    )
                ),
                compensation_0.share,
                self.context.crypto_extended_base_hash,
            )
        )

        self.assertTrue(
            compensation_1.proof.is_valid(
                first_selection.ciphertext,
                get_optional(
                    self.guardians[1].recovery_public_key_for(
                        self.guardians[2].object_id
                    )
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
            self.guardians[2].object_id,
            reconstructed_share,
            {
                self.guardians[0].object_id: compensation_0,
                self.guardians[1].object_id: compensation_1,
            },
        )

        # Decrypt the result
        result = decrypt_selection_with_decryption_shares(
            first_selection,
            {
                self.guardians[0].object_id: (
                    self.guardians[0].share_election_public_key().key,
                    share_0,
                ),
                self.guardians[1].object_id: (
                    self.guardians[1].share_election_public_key().key,
                    share_1,
                ),
                self.guardians[2].object_id: (
                    self.guardians[2].share_election_public_key().key,
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

        # find the first selection
        first_contest = [
            contest for contest in self.ciphertext_tally.contests.values()
        ][0]
        first_selection = list(first_contest.selections.values())[0]

        # precompute decryption shares for the guardians
        first_share = compute_decryption_share(
            self.guardians[0], self.ciphertext_tally, self.context
        )
        second_share = compute_decryption_share(
            self.guardians[1], self.ciphertext_tally, self.context
        )
        third_share = compute_decryption_share(
            self.guardians[2], self.ciphertext_tally, self.context
        )

        # build type: Dict[GUARDIAN_ID, Tuple[ELECTION_PUBLIC_KEY, TallyDecryptionShare]]
        shares = {
            self.guardians[0].object_id: (
                self.guardians[0].share_election_public_key().key,
                first_share.contests[first_contest.object_id].selections[
                    first_selection.object_id
                ],
            ),
            self.guardians[1].object_id: (
                self.guardians[1].share_election_public_key().key,
                second_share.contests[first_contest.object_id].selections[
                    first_selection.object_id
                ],
            ),
            self.guardians[2].object_id: (
                self.guardians[2].share_election_public_key().key,
                third_share.contests[first_contest.object_id].selections[
                    first_selection.object_id
                ],
            ),
        }

        # act
        result = decrypt_selection_with_decryption_shares(
            first_selection, shares, self.context.crypto_extended_base_hash
        )

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(
            self.expected_plaintext_tally[first_selection.object_id], result.tally
        )

    def test_decrypt_ballot_compensate_all_guardians_present(self):
        # Arrange
        # precompute decryption shares for the guardians
        plaintext_ballot = self.fake_cast_ballot
        encrypted_ballot = self.encrypted_fake_cast_ballot
        shares = {
            guardian.object_id: compute_decryption_share_for_ballot(
                guardian, encrypted_ballot, self.context
            )
            for guardian in self.guardians[0:3]
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

    def test_decrypt_ballot_compensate_missing_guardians(self):
        # Arrange
        # precompute decryption shares for the guardians
        plaintext_ballot = self.fake_cast_ballot
        encrypted_ballot = self.encrypted_fake_cast_ballot
        available_guardians = self.guardians[0:2]
        missing_guardian = self.guardians[2]
        missing_guardian_id = missing_guardian.object_id

        shares = {
            guardian.object_id: compute_decryption_share_for_ballot(
                guardian, encrypted_ballot, self.context
            )
            for guardian in available_guardians
        }
        compensated_shares = {
            guardian.object_id: compute_compensated_decryption_share_for_ballot(
                guardian,
                missing_guardian_id,
                encrypted_ballot,
                self.context,
                identity_auxiliary_decrypt,
            )
            for guardian in available_guardians
        }

        lagrange_coefficients = compute_lagrange_coefficients_for_guardians(
            [guardian.share_public_keys() for guardian in available_guardians]
        )
        public_key = (
            available_guardians[0]
            .guardian_election_public_keys()
            .get(missing_guardian_id)
        )

        reconstructed_share = reconstruct_decryption_share_for_ballot(
            missing_guardian_id,
            public_key,
            encrypted_ballot,
            compensated_shares,
            lagrange_coefficients,
        )

        all_shares = {**shares, missing_guardian_id: reconstructed_share}

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

    def test_decrypt_spoiled_ballots_all_guardians_present(self):
        # Arrange
        # precompute decryption shares for the guardians
        first_share = compute_decryption_share_for_ballots(
            self.guardians[0], list(self.ciphertext_ballots.values()), self.context
        )
        second_share = compute_decryption_share_for_ballots(
            self.guardians[1], list(self.ciphertext_ballots.values()), self.context
        )
        third_share = compute_decryption_share_for_ballots(
            self.guardians[2], list(self.ciphertext_ballots.values()), self.context
        )
        shares = {
            self.guardians[0].object_id: first_share,
            self.guardians[1].object_id: second_share,
            self.guardians[2].object_id: third_share,
        }

        # act
        result = decrypt_ballots(
            self.ciphertext_ballots,
            shares,
            self.context.crypto_extended_base_hash,
        )

        # assert
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

    def test_get_plaintext_tally_all_guardians_present_simple(self):
        # Arrange
        decrypter = DecryptionMediator(self.context, self.ciphertext_tally, {})

        # act
        for guardian in self.guardians:
            self.assertIsNotNone(decrypter.announce(guardian))

        decrypted_tallies = decrypter.get_plaintext_tally()
        spoiled_ballots = decrypter.get_plaintext_ballots()
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(spoiled_ballots)
        self.assertEqual(self.expected_plaintext_tally, result)

        # Verify we get the same tally back if we call again
        another_decrypted_tally = decrypter.get_plaintext_tally()

        self.assertEqual(decrypted_tallies, another_decrypted_tally)

    def test_get_plaintext_tally_compensate_missing_guardian_simple(self):

        # Arrange
        decrypter = DecryptionMediator(
            self.context,
            self.ciphertext_tally,
            self.ciphertext_ballots,
        )

        # Act

        self.assertIsNotNone(decrypter.announce(self.guardians[0]))
        self.assertIsNotNone(decrypter.announce(self.guardians[1]))

        decrypted_tallies = decrypter.get_plaintext_tally(identity_auxiliary_decrypt)
        self.assertIsNotNone(decrypted_tallies)
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        print(result)
        self.assertEqual(self.expected_plaintext_tally, result)

    @settings(
        deadline=timedelta(milliseconds=15000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=8,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(data(), integers(1, 3), integers(2, 5))
    def test_get_plaintext_tally_all_guardians_present(
        self, data, parties: int, contests: int
    ):
        # Arrange
        description = data.draw(election_descriptions(parties, contests))
        builder = ElectionBuilder(self.NUMBER_OF_GUARDIANS, self.QUORUM, description)
        internal_manifest, context = (
            builder.set_public_key(self.joint_public_key.joint_public_key)
            .set_commitment_hash(self.joint_public_key.commitment_hash)
            .build()
        )

        plaintext_ballots: List[PlaintextBallot] = data.draw(
            plaintext_voted_ballots(internal_manifest, randrange(3, 6))
        )
        plaintext_tallies = accumulate_plaintext_ballots(plaintext_ballots)

        encrypted_tally = self._generate_encrypted_tally(
            internal_manifest, context, plaintext_ballots
        )

        decrypter = DecryptionMediator(context, encrypted_tally, {})

        # act
        for guardian in self.guardians:
            self.assertIsNotNone(decrypter.announce(guardian))

        decrypted_tallies = decrypter.get_plaintext_tally()
        spoiled_ballots = decrypter.get_plaintext_ballots()
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(spoiled_ballots)
        self.assertEqual(plaintext_tallies, result)

    def _generate_encrypted_tally(
        self,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
        ballots: List[PlaintextBallot],
    ) -> CiphertextTally:

        # encrypt each ballot
        store = DataStore()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(
                ballot, internal_manifest, context, int_to_q_unchecked(1)
            )
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                from_ciphertext_ballot(encrypted_ballot, BallotBoxState.CAST),
            )

        tally = tally_ballots(store, internal_manifest, context)
        self.assertIsNotNone(tally)
        return get_optional(tally)

    def _convert_to_selections(self, tally: PlaintextTally) -> Dict[str, int]:
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.contests.items():
            for selection_id, selection in contest.selections.items():
                plaintext_selections[selection_id] = selection.tally

        return plaintext_selections
