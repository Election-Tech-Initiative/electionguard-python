from unittest import TestCase, skip
from datetime import timedelta
from typing import Dict, List
from random import Random, randrange

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers, data

from electionguard.ballot import PlaintextBallot, from_ciphertext_ballot
from electionguard.ballot_store import BallotStore

from electionguard.ballot_box import BallotBox, BallotBoxState
from electionguard.decryption_mediator import (
    DecryptionMediator,
    PlaintextTally,
    PlaintextTallyContest,
    PlaintextTallySelection,
    compute_decryption_share,
    _compute_decryption_for_selection,
)
from electionguard.decryption_share import DecryptionShare, BallotDecryptionShare
from electionguard.election import (
    CiphertextElectionContext,
    ElectionDescription,
    InternalElectionDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from electionguard.election_builder import ElectionBuilder
from electionguard.encrypt import EncryptionDevice, EncryptionMediator, encrypt_ballot

from electionguard.group import ElementModP, int_to_q_unchecked
from electionguard.guardian import Guardian
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionPartialKeyVerification,
    GuardianPair,
)
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.tally import CiphertextTally, tally_ballots, tally_ballot
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
            self.guardians.append(
                Guardian("guardian_" + str(i), i, self.NUMBER_OF_GUARDIANS, self.QUORUM)
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
        builder.set_public_key(self.joint_public_key)
        self.metadata, self.encryption_context = get_optional(builder.build())

        self.encryption_device = EncryptionDevice("location")
        self.ballot_marking_device = EncryptionMediator(
            self.metadata, self.encryption_context, self.encryption_device
        )

        # get some fake ballots
        self.fake_cast_ballot = ballot_factory.get_fake_ballot(
            self.metadata, "some-unique-ballot-id-cast"
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
            [self.fake_cast_ballot]
        )

        # Fill in any missing selections that were not made on any ballots
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
                self.encryption_context.crypto_extended_base_hash, self.joint_public_key
            )
        )

        # configure the ballot box
        ballot_store = BallotStore()
        ballot_box = BallotBox(self.metadata, self.encryption_context, ballot_store)
        ballot_box.cast(encrypted_fake_cast_ballot)
        ballot_box.spoil(encrypted_fake_spoiled_ballot)

        # generate encrypted tally
        self.ciphertext_tally = tally_ballots(
            ballot_store, self.metadata, self.encryption_context
        )

    def test_announce(self):
        # Arrange
        subject = DecryptionMediator(
            self.metadata, self.encryption_context, self.ciphertext_tally
        )

        # act
        result = subject.announce(self.guardians[0])

        # assert
        self.assertIsNotNone(result)

        # Can only announce once
        self.assertIsNone(subject.announce(self.guardians[0]))

        # Cannot submit another share internally
        self.assertFalse(
            subject._submit_decryption_share(
                DecryptionShare(self.guardians[0].object_id, {}, {})
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
        result = _compute_decryption_for_selection(
            self.guardians[0], first_selection, self.encryption_context
        )

        # assert
        self.assertIsNotNone(result)

    def test_decrypt_selection(self):
        # Arrange

        # find the first selection
        first_contest = [contest for contest in self.ciphertext_tally.cast.values()][0]
        first_selection = list(first_contest.tally_selections.values())[0]

        # precompute decryption shares for the guardians
        first_share = compute_decryption_share(
            self.guardians[0], self.ciphertext_tally, self.encryption_context
        )
        second_share = compute_decryption_share(
            self.guardians[1], self.ciphertext_tally, self.encryption_context
        )
        third_share = compute_decryption_share(
            self.guardians[2], self.ciphertext_tally, self.encryption_context
        )
        shares = {
            self.guardians[0]
            .object_id: first_share.contests[first_contest.object_id]
            .selections[first_selection.object_id]
            .share,
            self.guardians[1]
            .object_id: second_share.contests[first_contest.object_id]
            .selections[first_selection.object_id]
            .share,
            self.guardians[2]
            .object_id: third_share.contests[first_contest.object_id]
            .selections[first_selection.object_id]
            .share,
        }

        subject = DecryptionMediator(
            self.metadata, self.encryption_context, self.ciphertext_tally
        )

        # act
        result = subject._decrypt_selection(first_selection, shares)

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(
            self.expected_plaintext_tally[first_selection.object_id], result.plaintext
        )

    def test_decrypt_spoiled_ballots(self):
        # Arrange
        # precompute decryption shares for the guardians
        first_share = compute_decryption_share(
            self.guardians[0], self.ciphertext_tally, self.encryption_context
        )
        second_share = compute_decryption_share(
            self.guardians[1], self.ciphertext_tally, self.encryption_context
        )
        third_share = compute_decryption_share(
            self.guardians[2], self.ciphertext_tally, self.encryption_context
        )
        shares = {
            self.guardians[0].object_id: first_share,
            self.guardians[1].object_id: second_share,
            self.guardians[2].object_id: third_share,
        }

        subject = DecryptionMediator(
            self.metadata, self.encryption_context, self.ciphertext_tally
        )

        # act
        result = subject._decrypt_spoiled_ballots(
            self.ciphertext_tally.spoiled_ballots, shares
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
        subject = DecryptionMediator(
            self.metadata, self.encryption_context, self.ciphertext_tally
        )

        # act
        for guardian in self.guardians:
            self.assertIsNotNone(subject.announce(guardian))

        decrypted_tallies = subject.get_plaintext_tally()
        result = self._convert_to_selections(decrypted_tallies)

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(self.expected_plaintext_tally, result)

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=1,
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
