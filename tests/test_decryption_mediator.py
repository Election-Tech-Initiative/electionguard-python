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

NUMBER_OF_GUARDIANS = 3
QUORUM = 2
CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_1_ID = "Guardian 1"
GUARDIAN_2_ID = "Guardian 2"
GUARDIAN_3_ID = "Guardian 3"
GUARDIAN_1 = Guardian(GUARDIAN_1_ID, 1, NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_2 = Guardian(GUARDIAN_2_ID, 2, NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_3 = Guardian(GUARDIAN_3_ID, 3, NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_1.save_guardian_public_keys(GUARDIAN_2.share_public_keys())
GUARDIAN_1.save_guardian_public_keys(GUARDIAN_3.share_public_keys())
GUARDIAN_2.save_guardian_public_keys(GUARDIAN_1.share_public_keys())
GUARDIAN_2.save_guardian_public_keys(GUARDIAN_3.share_public_keys())
GUARDIAN_3.save_guardian_public_keys(GUARDIAN_1.share_public_keys())
GUARDIAN_3.save_guardian_public_keys(GUARDIAN_2.share_public_keys())
GUARDIAN_1.generate_election_partial_key_backups()
GUARDIAN_2.generate_election_partial_key_backups()
GUARDIAN_3.generate_election_partial_key_backups()


class TestDecryptionMediator(TestCase):
    def setUp(self):
        self.key_ceremony = KeyCeremonyMediator(CEREMONY_DETAILS)
        self.key_ceremony.confirm_presence_of_guardian(GUARDIAN_1.share_public_keys())
        self.key_ceremony.confirm_presence_of_guardian(GUARDIAN_2.share_public_keys())
        self.key_ceremony.confirm_presence_of_guardian(GUARDIAN_3.share_public_keys())

        self.assertTrue(self.key_ceremony.all_guardians_in_attendance())

        # share the aux keys
        self.key_ceremony.receive_auxiliary_public_key(
            GUARDIAN_1.share_auxiliary_public_key()
        )
        self.key_ceremony.receive_auxiliary_public_key(
            GUARDIAN_2.share_auxiliary_public_key()
        )
        self.key_ceremony.receive_auxiliary_public_key(
            GUARDIAN_3.share_auxiliary_public_key()
        )

        self.assertTrue(self.key_ceremony.all_auxiliary_public_keys_available())

        # share the election keys
        self.key_ceremony.receive_election_public_key(
            GUARDIAN_1.share_election_public_key()
        )
        self.key_ceremony.receive_election_public_key(
            GUARDIAN_2.share_election_public_key()
        )
        self.key_ceremony.receive_election_public_key(
            GUARDIAN_3.share_election_public_key()
        )

        self.assertTrue(self.key_ceremony.all_election_public_keys_available())

        # Share the partial key backups
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_1.share_election_partial_key_backup(GUARDIAN_2_ID)
        )
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_1.share_election_partial_key_backup(GUARDIAN_3_ID)
        )
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_2.share_election_partial_key_backup(GUARDIAN_1_ID)
        )
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_2.share_election_partial_key_backup(GUARDIAN_3_ID)
        )
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_3.share_election_partial_key_backup(GUARDIAN_1_ID)
        )
        self.key_ceremony.receive_election_partial_key_backup(
            GUARDIAN_3.share_election_partial_key_backup(GUARDIAN_2_ID)
        )

        self.assertTrue(self.key_ceremony.all_election_partial_key_backups_available())

        # save the backups
        GUARDIAN_1.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_1_ID
            )[0]
        )
        GUARDIAN_1.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_1_ID
            )[1]
        )
        GUARDIAN_2.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_2_ID
            )[0]
        )
        GUARDIAN_2.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_2_ID
            )[1]
        )
        GUARDIAN_3.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_3_ID
            )[0]
        )
        GUARDIAN_3.save_election_partial_key_backup(
            self.key_ceremony.share_election_partial_key_backups_to_guardian(
                GUARDIAN_3_ID
            )[1]
        )

        # verify the keys
        verification1_2 = GUARDIAN_1.verify_election_partial_key_backup(GUARDIAN_2_ID)
        verification1_3 = GUARDIAN_1.verify_election_partial_key_backup(GUARDIAN_3_ID)
        verification2_1 = GUARDIAN_2.verify_election_partial_key_backup(GUARDIAN_1_ID)
        verification2_3 = GUARDIAN_2.verify_election_partial_key_backup(GUARDIAN_3_ID)
        verification3_1 = GUARDIAN_3.verify_election_partial_key_backup(GUARDIAN_1_ID)
        verification3_2 = GUARDIAN_3.verify_election_partial_key_backup(GUARDIAN_2_ID)

        self.key_ceremony.receive_election_partial_key_verification(verification1_2)
        self.key_ceremony.receive_election_partial_key_verification(verification1_3)
        self.key_ceremony.receive_election_partial_key_verification(verification2_1)
        self.key_ceremony.receive_election_partial_key_verification(verification2_3)
        self.key_ceremony.receive_election_partial_key_verification(verification3_1)
        self.key_ceremony.receive_election_partial_key_verification(verification3_2)

        self.assertTrue(
            self.key_ceremony.all_election_partial_key_verifications_received()
        )
        self.assertTrue(self.key_ceremony.all_election_partial_key_backups_verified())

        self.joint_public_key = self.key_ceremony.publish_joint_key()

        # setup the election
        self.election = election_factory.get_fake_election()
        builder = ElectionBuilder(NUMBER_OF_GUARDIANS, QUORUM, self.election)
        self.metadata, self.encryption_context = builder.set_public_key(
            self.joint_public_key
        ).build()

        self.encryption_device = EncryptionDevice("location")
        self.ballot_marking_device = EncryptionMediator(
            self.metadata, self.encryption_context, self.encryption_device
        )

        # get some fake ballots
        fake_ballot = election_factory.get_fake_ballot(self.metadata)
        self.assertTrue(fake_ballot.is_valid(self.metadata.ballot_styles[0].object_id))
        self.expected_plaintext_tally = accumulate_plaintext_ballots([fake_ballot])

        encrypted_ballot = self.ballot_marking_device.encrypt(fake_ballot)

        # configure the ballot box
        ballot_store = BallotStore()
        ballot_box = BallotBox(self.metadata, self.encryption_context, ballot_store)
        ballot_box.cast(encrypted_ballot)

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
        result = subject.announce(GUARDIAN_1)

        # assert
        self.assertIsNotNone(result)

        # Can only announce once
        self.assertIsNone(subject.announce(GUARDIAN_1))

        # Cannot submit another share internally
        self.assertFalse(
            subject._submit_decryption_share(DecryptionShare(GUARDIAN_1_ID, {}, {}))
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
            GUARDIAN_1, first_selection, self.encryption_context
        )

        # assert
        self.assertIsNotNone(result)

    def test_decrypt_selection(self):
        # Arrange
        # precompute decryption shares for the guardians
        first_share = compute_decryption_share(
            GUARDIAN_1, self.ciphertext_tally, self.encryption_context
        )
        second_share = compute_decryption_share(
            GUARDIAN_2, self.ciphertext_tally, self.encryption_context
        )
        third_share = compute_decryption_share(
            GUARDIAN_3, self.ciphertext_tally, self.encryption_context
        )
        shares = {
            GUARDIAN_1_ID: first_share,
            GUARDIAN_2_ID: second_share,
            GUARDIAN_3_ID: third_share,
        }

        subject = DecryptionMediator(
            self.metadata, self.encryption_context, self.ciphertext_tally
        )

        # find the first selection
        first_selection = [
            selection
            for contest in self.ciphertext_tally.cast.values()
            for selection in contest.tally_selections.values()
        ][0]

        # act
        result = subject._decrypt_selection(first_selection, shares)

        # assert
        self.assertIsNotNone(result)
        self.assertEqual(
            self.expected_plaintext_tally[first_selection.object_id], result.plaintext
        )

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
        builder = ElectionBuilder(NUMBER_OF_GUARDIANS, QUORUM, description)
        metadata, context = builder.set_public_key(self.joint_public_key).build()

        plaintext_ballots: List[PlaintextBallot] = data.draw(
            plaintext_voted_ballots(metadata, randrange(3, 6))
        )
        plaintext_tallies = accumulate_plaintext_ballots(plaintext_ballots)
        print(plaintext_tallies)

        encrypted_tally = self._generate_encrypted_tally(
            metadata, context, plaintext_ballots
        )

        subject = DecryptionMediator(metadata, context, encrypted_tally)

        # act
        self.assertIsNotNone(subject.announce(GUARDIAN_1))
        self.assertIsNotNone(subject.announce(GUARDIAN_2))
        self.assertIsNotNone(subject.announce(GUARDIAN_3))

        decrypted_tallies = subject.get_plaintext_tally()
        result = self._convert_to_selections(decrypted_tallies)
        print(result)

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
