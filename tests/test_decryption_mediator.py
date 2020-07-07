from unittest import TestCase
from datetime import timedelta
from typing import Dict, List
from random import randrange

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers, data

from electionguard.ballot import PlaintextBallot, from_ciphertext_ballot
from electionguard.ballot_store import BallotStore

from electionguard.ballot_box import BallotBox, BallotBoxState
from electionguard.decrypt_with_shares import (
    decrypt_selection_with_decryption_shares,
    decrypt_spoiled_ballots,
)
from electionguard.decryption import (
    compute_decryption_share,
    compute_decryption_share_for_selection,
    compute_compensated_decryption_share_for_selection,
)
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.decryption_share import (
    CiphertextDecryptionSelection,
    TallyDecryptionShare,
)
from electionguard.election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from electionguard.election_builder import ElectionBuilder
from electionguard.encrypt import EncryptionDevice, EncryptionMediator, encrypt_ballot
from electionguard.election_polynomial import compute_lagrange_coefficient

from electionguard.group import (
    int_to_q_unchecked,
    ZERO_MOD_P,
    mult_p,
    pow_p,
)
from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
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


class TestDecryptionMediator(TestCase):
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

        self.key_ceremony.orchestrate()
        self.key_ceremony.verify()

        self.joint_public_key = self.key_ceremony.publish_joint_key()
        self.assertIsNotNone(self.joint_public_key)

        # setup the election
        self.election = election_factory.get_fake_election()
        builder = ElectionBuilder(self.NUMBER_OF_GUARDIANS, self.QUORUM, self.election)

        self.assertIsNone(builder.build())  # Can't build without the public key

        builder.set_public_key(self.joint_public_key)
        self.metadata, self.context = get_optional(builder.build())

        self.encryption_device = EncryptionDevice("location")
        self.ballot_marking_device = EncryptionMediator(
            self.metadata, self.context, self.encryption_device
        )

        # get some fake ballots
        self.fake_cast_ballot = ballot_factory.get_fake_ballot(
            self.metadata, "some-unique-ballot-id-cast"
        )
        self.more_fake_ballots = []
        for i in range(10):
            self.more_fake_ballots.append(
                ballot_factory.get_fake_ballot(
                    self.metadata, f"some-unique-ballot-id-cast{i}"
                )
            )
        self.fake_spoiled_ballot = ballot_factory.get_fake_ballot(
            self.metadata, "some-unique-ballot-id-spoiled"
        )
        self.assertTrue(
            self.fake_cast_ballot.is_valid(self.metadata.ballot_styles[0].object_id)
        )
        self.assertTrue(
            self.fake_spoiled_ballot.is_valid(self.metadata.ballot_styles[0].object_id)
        )
        self.expected_plaintext_tally = accumulate_plaintext_ballots(
            [self.fake_cast_ballot] + self.more_fake_ballots
        )

        # Fill in the expected values with any missing selections
        # that were not made on any ballots
        selection_ids = set(
            [
                selection.object_id
                for contest in self.metadata.contests
                for selection in contest.ballot_selections
            ]
        )

        missing_selection_ids = selection_ids.difference(
            set(self.expected_plaintext_tally)
        )

        for id in missing_selection_ids:
            self.expected_plaintext_tally[id] = 0

        # Encrypt
        encrypted_fake_cast_ballot = self.ballot_marking_device.encrypt(
            self.fake_cast_ballot
        )
        encrypted_fake_spoiled_ballot = self.ballot_marking_device.encrypt(
            self.fake_spoiled_ballot
        )
        self.assertIsNotNone(encrypted_fake_cast_ballot)
        self.assertIsNotNone(encrypted_fake_spoiled_ballot)
        self.assertTrue(
            encrypted_fake_cast_ballot.is_valid_encryption(
                self.context.crypto_extended_base_hash, self.joint_public_key
            )
        )

        # encrypt some more fake ballots
        self.more_fake_encrypted_ballots = []
        for fake_ballot in self.more_fake_ballots:
            self.more_fake_encrypted_ballots.append(
                self.ballot_marking_device.encrypt(fake_ballot)
            )

        # configure the ballot box
        ballot_store = BallotStore()
        ballot_box = BallotBox(self.metadata, self.context, ballot_store)
        ballot_box.cast(encrypted_fake_cast_ballot)
        ballot_box.spoil(encrypted_fake_spoiled_ballot)

        # Cast some more fake ballots
        for fake_ballot in self.more_fake_encrypted_ballots:
            ballot_box.cast(fake_ballot)

        # generate encrypted tally
        self.ciphertext_tally = tally_ballots(ballot_store, self.metadata, self.context)

    def test_announce(self):
        # Arrange
        subject = DecryptionMediator(self.metadata, self.context, self.ciphertext_tally)

        # act
        result = subject.announce(self.guardians[0])

        # assert
        self.assertIsNotNone(result)

        # Can only announce once
        self.assertIsNotNone(subject.announce(self.guardians[0]))

        # Cannot submit another share internally
        self.assertFalse(
            subject._submit_decryption_share(
                TallyDecryptionShare(self.guardians[0].object_id, ZERO_MOD_P, {}, {})
            )
        )

        # Cannot get plaintext tally without a quorum
        self.assertIsNone(subject.get_plaintext_tally())

    def test_compute_selection(self):
        # Arrange
        first_selection = [
            selection
            for contest in self.ciphertext_tally.cast.values()
            for selection in contest.tally_selections.values()
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
            for contest in self.ciphertext_tally.cast.values()
            for selection in contest.tally_selections.values()
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
            for contest in self.ciphertext_tally.cast.values()
            for selection in contest.tally_selections.values()
        ][0]

        # Compute lagrange coefficients for the guardians that are present
        lagrange_0 = compute_lagrange_coefficient(
            self.guardians[0].sequence_order, *[self.guardians[1].sequence_order],
        )
        lagrange_1 = compute_lagrange_coefficient(
            self.guardians[1].sequence_order, *[self.guardians[0].sequence_order],
        )

        print(
            f"lagrange: sequence_orders: ({self.guardians[0].sequence_order}, {self.guardians[1].sequence_order}, {self.guardians[2].sequence_order})\n"
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
        )

        compensation_1 = compute_compensated_decryption_share_for_selection(
            self.guardians[1],
            self.guardians[2].object_id,
            first_selection,
            self.context,
        )

        self.assertIsNotNone(compensation_0)
        self.assertIsNotNone(compensation_1)

        print("\nSHARES:")
        print(compensation_0)
        print(compensation_1)

        # Check the share proofs
        self.assertTrue(
            compensation_0.proof.is_valid(
                first_selection.message,
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
                first_selection.message,
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

        share_2 = CiphertextDecryptionSelection(
            first_selection.object_id,
            self.guardians[2].object_id,
            first_selection.description_hash,
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
            result.plaintext, self.expected_plaintext_tally[first_selection.object_id]
        )

    def test_decrypt_selection_all_present(self):
        # Arrange

        # find the first selection
        first_contest = [contest for contest in self.ciphertext_tally.cast.values()][0]
        first_selection = list(first_contest.tally_selections.values())[0]

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
            self.expected_plaintext_tally[first_selection.object_id], result.plaintext
        )

    def test_decrypt_spoiled_ballots_all_guardians_present(self):
        # Arrange
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
        shares = {
            self.guardians[0].object_id: first_share,
            self.guardians[1].object_id: second_share,
            self.guardians[2].object_id: third_share,
        }

        subject = DecryptionMediator(self.metadata, self.context, self.ciphertext_tally)

        # act
        result = decrypt_spoiled_ballots(
            self.ciphertext_tally.spoiled_ballots,
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
                    spoiled_ballot[contest.object_id]
                    .selections[selection.object_id]
                    .plaintext,
                    result[self.fake_spoiled_ballot.object_id][contest.object_id]
                    .selections[selection.object_id]
                    .plaintext,
                )

    def test_get_plaintext_tally_all_guardians_present_simple(self):
        # Arrange
        subject = DecryptionMediator(self.metadata, self.context, self.ciphertext_tally)

        # act
        for guardian in self.guardians:
            self.assertIsNotNone(subject.announce(guardian))

        decrypted_tallies = subject.get_plaintext_tally()
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(self.expected_plaintext_tally, result)

        # Verify we get the same tally back if we call again
        another_decrypted_tally = subject.get_plaintext_tally()

        self.assertEqual(decrypted_tallies, another_decrypted_tally)

    def test_get_plaintext_tally_compensate_missing_guardian_simple(self):

        # Arrange
        subject = DecryptionMediator(self.metadata, self.context, self.ciphertext_tally)

        # Act

        self.assertIsNotNone(subject.announce(self.guardians[0]))
        self.assertIsNotNone(subject.announce(self.guardians[1]))

        # explicitly compensate to demonstrate that this is possible, but not required
        self.assertIsNotNone(subject.compensate(self.guardians[2].object_id))

        decrypted_tallies = subject.get_plaintext_tally()
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
        metadata, context = builder.set_public_key(self.joint_public_key).build()

        plaintext_ballots: List[PlaintextBallot] = data.draw(
            plaintext_voted_ballots(metadata, randrange(3, 6))
        )
        plaintext_tallies = accumulate_plaintext_ballots(plaintext_ballots)

        encrypted_tally = self._generate_encrypted_tally(
            metadata, context, plaintext_ballots
        )

        subject = DecryptionMediator(metadata, context, encrypted_tally)

        # act
        for guardian in self.guardians:
            self.assertIsNotNone(subject.announce(guardian))

        decrypted_tallies = subject.get_plaintext_tally()
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(plaintext_tallies, result)

    def _generate_encrypted_tally(
        self,
        metadata: InternalElectionDescription,
        context: CiphertextElectionContext,
        ballots: List[PlaintextBallot],
    ) -> CiphertextTally:

        # encrypt each ballot
        store = BallotStore()
        for ballot in ballots:
            encrypted_ballot = encrypt_ballot(
                ballot, metadata, context, int_to_q_unchecked(1)
            )
            self.assertIsNotNone(encrypted_ballot)
            # add to the ballot store
            store.set(
                encrypted_ballot.object_id,
                from_ciphertext_ballot(encrypted_ballot, BallotBoxState.CAST),
            )

        tally = tally_ballots(store, metadata, context)
        self.assertIsNotNone(tally)
        return get_optional(tally)

    def _convert_to_selections(self, tally: PlaintextTally) -> Dict[str, int]:
        plaintext_selections: Dict[str, int] = {}
        for _, contest in tally.contests.items():
            for selection_id, selection in contest.selections.items():
                plaintext_selections[selection_id] = selection.plaintext

        return plaintext_selections
