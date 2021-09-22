from tests.base_test_case import BaseTestCase

from electionguard.guardian import Guardian
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionPartialKeyVerification,
)
from electionguard.key_ceremony_mediator import KeyCeremonyMediator, GuardianPair
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)
from electionguard_tools.helpers.identity_encrypt import identity_auxiliary_decrypt

NUMBER_OF_GUARDIANS = 2
QUORUM = 2
CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_1_ID = "Guardian 1"
GUARDIAN_2_ID = "Guardian 2"


class TestKeyCeremonyMediator(BaseTestCase):
    """Key ceremony mediator tests"""

    GUARDIAN_1 = None
    GUARDIAN_2 = None
    GUARDIANS = []

    def setUp(self) -> None:
        super().setUp()
        self.GUARDIAN_1 = Guardian(GUARDIAN_1_ID, 1, NUMBER_OF_GUARDIANS, QUORUM)
        self.GUARDIAN_2 = Guardian(GUARDIAN_2_ID, 2, NUMBER_OF_GUARDIANS, QUORUM)
        self.GUARDIANS = [self.GUARDIAN_1, self.GUARDIAN_2]

    def test_reset(self):
        # Arrange
        mediator = KeyCeremonyMediator("mediator_reset", CEREMONY_DETAILS)
        new_ceremony_details = CeremonyDetails(3, 3)

        mediator.reset(new_ceremony_details)
        self.assertEqual(mediator.ceremony_details, new_ceremony_details)

    def test_take_attendance(self):
        """Round 1: Mediator takes attendance and guardians announce"""

        # Arrange
        mediator = KeyCeremonyMediator("mediator_attendance", CEREMONY_DETAILS)

        # Act
        mediator.announce(self.GUARDIAN_1.share_public_keys())

        # Assert
        self.assertFalse(mediator.all_guardians_announced())

        # Act
        mediator.announce(self.GUARDIAN_2.share_public_keys())

        # Assert
        self.assertTrue(mediator.all_guardians_announced())

        # Act
        guardian_key_sets = mediator.share_announced()

        # Assert
        self.assertIsNotNone(guardian_key_sets)
        self.assertEqual(len(guardian_key_sets), NUMBER_OF_GUARDIANS)

    def test_exchange_of_backups(self):
        """Round 2: Exchange of election partial key backups"""

        # Arrange
        mediator = KeyCeremonyMediator("mediator_backups_exchange", CEREMONY_DETAILS)
        KeyCeremonyOrchestrator.perform_round_1(self.GUARDIANS, mediator)

        # Round 2 - Guardians Only
        self.GUARDIAN_1.generate_election_partial_key_backups()
        self.GUARDIAN_2.generate_election_partial_key_backups()
        backup_from_1_for_2 = self.GUARDIAN_1.share_election_partial_key_backup(
            GUARDIAN_2_ID
        )
        backup_from_2_for_1 = self.GUARDIAN_2.share_election_partial_key_backup(
            GUARDIAN_1_ID
        )

        # Act
        mediator.receive_backups([backup_from_1_for_2])

        # Assert
        self.assertFalse(mediator.all_backups_available())

        # Act
        mediator.receive_backups([backup_from_2_for_1])

        # Assert
        self.assertTrue(mediator.all_backups_available())

        # Act
        guardian1_backups = mediator.share_backups(GUARDIAN_1_ID)
        guardian2_backups = mediator.share_backups(GUARDIAN_2_ID)

        # Assert
        self.assertIsNotNone(guardian1_backups)
        self.assertIsNotNone(guardian2_backups)
        self.assertEqual(len(guardian1_backups), 1)
        self.assertEqual(len(guardian2_backups), 1)
        for backup in guardian1_backups:
            self.assertEqual(backup.designated_id, GUARDIAN_1_ID)
        for backup in guardian2_backups:
            self.assertEqual(backup.designated_id, GUARDIAN_2_ID)
        self.assertEqual(guardian1_backups[0], backup_from_2_for_1)
        self.assertEqual(guardian2_backups[0], backup_from_1_for_2)

    # Partial Key Verifications
    def test_partial_key_backup_verification_success(self):
        """
        Test for the happy path of the verification process where each key is successfully verified and no bad actors.
        """
        # Arrange
        mediator = KeyCeremonyMediator("mediator_verification", CEREMONY_DETAILS)
        KeyCeremonyOrchestrator.perform_round_1(self.GUARDIANS, mediator)
        KeyCeremonyOrchestrator.perform_round_2(self.GUARDIANS, mediator)

        # Round 3 - Guardians only
        verification1 = self.GUARDIAN_1.verify_election_partial_key_backup(
            GUARDIAN_2_ID, identity_auxiliary_decrypt
        )
        verification2 = self.GUARDIAN_2.verify_election_partial_key_backup(
            GUARDIAN_1_ID, identity_auxiliary_decrypt
        )

        # Act
        mediator.receive_backup_verifications([verification1])

        # Assert
        self.assertFalse(mediator.get_verification_state().all_sent)
        self.assertFalse(mediator.all_backups_verified())
        self.assertIsNone(mediator.publish_joint_key())

        # Act
        mediator.receive_backup_verifications([verification2])
        joint_key = mediator.publish_joint_key()

        # Assert
        self.assertTrue(mediator.get_verification_state().all_sent)
        self.assertTrue(mediator.all_backups_verified())
        self.assertIsNotNone(joint_key)

    def test_partial_key_backup_verification_failure(self):
        """
        In this case, the recipient guardian does not correctly verify the sent key backup.
        This failed verificaton requires the sender create a challenge and a new verifier
        aka another guardian must verify this challenge.
        """
        # Arrange
        mediator = KeyCeremonyMediator("mediator_challenge", CEREMONY_DETAILS)
        KeyCeremonyOrchestrator.perform_round_1(self.GUARDIANS, mediator)
        KeyCeremonyOrchestrator.perform_round_2(self.GUARDIANS, mediator)

        # Round 3 - Guardians only
        verification1 = self.GUARDIAN_1.verify_election_partial_key_backup(
            GUARDIAN_2_ID, identity_auxiliary_decrypt
        )

        # Act
        failed_verification2 = ElectionPartialKeyVerification(
            GUARDIAN_1_ID,
            GUARDIAN_2_ID,
            GUARDIAN_2_ID,
            False,
        )
        mediator.receive_backup_verifications([verification1, failed_verification2])

        state = mediator.get_verification_state()

        # Assert
        self.assertTrue(state.all_sent)
        self.assertFalse(state.all_verified)
        self.assertIsNone(mediator.publish_joint_key())
        self.assertEqual(len(state.failed_verifications), 1)
        self.assertEqual(
            state.failed_verifications[0], GuardianPair(GUARDIAN_1_ID, GUARDIAN_2_ID)
        )

        # Act
        challenge = self.GUARDIAN_1.publish_election_backup_challenge(GUARDIAN_2_ID)
        mediator.verify_challenge(challenge)
        new_state = mediator.get_verification_state()
        all_verified = mediator.all_backups_verified()
        joint_key = mediator.publish_joint_key()

        # Assert
        self.assertTrue(new_state.all_sent)
        self.assertTrue(new_state.all_verified)
        self.assertEqual(len(new_state.failed_verifications), 0)
        self.assertTrue(all_verified)
        self.assertIsNotNone(joint_key)
