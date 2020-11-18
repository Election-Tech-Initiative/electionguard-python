from unittest import TestCase

from electionguard.guardian import Guardian
from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionPartialKeyVerification,
    GuardianPair,
)
from electionguard.key_ceremony_mediator import KeyCeremonyMediator

identity_auxiliary_decrypt = lambda message, public_key: message
identity_auxiliary_encrypt = lambda message, private_key: message

NUMBER_OF_GUARDIANS = 2
QUORUM = 2
CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_1_ID = "Guardian 1"
GUARDIAN_2_ID = "Guardian 2"
VERIFIER_ID = "Guardian 3"
GUARDIAN_1 = Guardian(GUARDIAN_1_ID, 1, NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_2 = Guardian(GUARDIAN_2_ID, 2, NUMBER_OF_GUARDIANS, QUORUM)
VERIFIER = Guardian(VERIFIER_ID, 3, NUMBER_OF_GUARDIANS, QUORUM)
GUARDIAN_1.save_guardian_public_keys(GUARDIAN_2.share_public_keys())
GUARDIAN_2.save_guardian_public_keys(GUARDIAN_1.share_public_keys())
VERIFIER.save_guardian_public_keys(GUARDIAN_2.share_public_keys())
GUARDIAN_1.generate_election_partial_key_backups(identity_auxiliary_encrypt)
GUARDIAN_2.generate_election_partial_key_backups(identity_auxiliary_encrypt)


class TestKeyCeremonyMediator(TestCase):
    def test_reset(self):
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)
        new_ceremony_details = CeremonyDetails(3, 3)

        mediator.reset(new_ceremony_details)
        self.assertEqual(mediator.ceremony_details, new_ceremony_details)

    def test_mediator_takes_attendance(self):
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)

        # Act
        mediator.confirm_presence_of_guardian(GUARDIAN_1.share_public_keys())

        # Assert
        self.assertFalse(mediator.all_guardians_in_attendance())

        # Act
        mediator.confirm_presence_of_guardian(GUARDIAN_2.share_public_keys())

        # Assert
        self.assertTrue(mediator.all_guardians_in_attendance())

        # Act
        guardians = mediator.share_guardians_in_attendance()

        # Assert
        self.assertIsNotNone(guardians)
        self.assertEqual(len(guardians), NUMBER_OF_GUARDIANS)

    def test_exchange_of_auxiliary_public_keys(self):
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)

        # Act
        mediator.receive_auxiliary_public_key(GUARDIAN_1.share_auxiliary_public_key())

        # Assert
        self.assertFalse(mediator.all_auxiliary_public_keys_available())
        partial_list = mediator.share_auxiliary_public_keys()
        self.assertIsNotNone(partial_list)
        self.assertEqual(len(partial_list), 1)

        # Act
        mediator.receive_auxiliary_public_key(GUARDIAN_2.share_auxiliary_public_key())

        # Assert
        self.assertTrue(mediator.all_auxiliary_public_keys_available())
        partial_list = mediator.share_auxiliary_public_keys()
        self.assertIsNotNone(partial_list)
        self.assertEqual(len(partial_list), 2)

    # Election Public Keys
    def test_exchange_of_election_public_keys(self):
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)

        # Act
        mediator.receive_election_public_key(GUARDIAN_1.share_election_public_key())

        # Assert
        self.assertFalse(mediator.all_election_public_keys_available())
        partial_list = mediator.share_election_public_keys()
        self.assertIsNotNone(partial_list)
        self.assertEqual(len(partial_list), 1)

        # Act
        mediator.receive_election_public_key(GUARDIAN_2.share_election_public_key())

        # Assert
        self.assertTrue(mediator.all_election_public_keys_available())
        partial_list = mediator.share_election_public_keys()
        self.assertIsNotNone(partial_list)
        self.assertEqual(len(partial_list), 2)

    # Election Partial Key Backups
    def test_exchange_of_election_partial_key_backup(self):
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)
        mediator.confirm_presence_of_guardian(GUARDIAN_1.share_public_keys())
        mediator.confirm_presence_of_guardian(GUARDIAN_2.share_public_keys())
        backup_from_1_for_2 = GUARDIAN_1.share_election_partial_key_backup(
            GUARDIAN_2_ID
        )
        backup_from_2_for_1 = GUARDIAN_2.share_election_partial_key_backup(
            GUARDIAN_1_ID
        )

        # Act
        mediator.receive_election_partial_key_backup(backup_from_1_for_2)

        # Assert
        self.assertFalse(mediator.all_election_partial_key_backups_available())

        # Act
        mediator.receive_election_partial_key_backup(backup_from_2_for_1)

        # Assert
        self.assertTrue(mediator.all_election_partial_key_backups_available())

        # Act
        guardian1_backups = mediator.share_election_partial_key_backups_to_guardian(
            GUARDIAN_1_ID
        )
        guardian2_backups = mediator.share_election_partial_key_backups_to_guardian(
            GUARDIAN_2_ID
        )

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
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)
        mediator.confirm_presence_of_guardian(GUARDIAN_1.share_public_keys())
        mediator.confirm_presence_of_guardian(GUARDIAN_2.share_public_keys())
        mediator.receive_election_partial_key_backup(
            GUARDIAN_1.share_election_partial_key_backup(GUARDIAN_2_ID)
        )
        mediator.receive_election_partial_key_backup(
            GUARDIAN_2.share_election_partial_key_backup(GUARDIAN_1_ID)
        )
        GUARDIAN_1.save_election_partial_key_backup(
            mediator.share_election_partial_key_backups_to_guardian(GUARDIAN_1_ID)[0]
        )
        GUARDIAN_2.save_election_partial_key_backup(
            mediator.share_election_partial_key_backups_to_guardian(GUARDIAN_2_ID)[0]
        )
        verification1 = GUARDIAN_1.verify_election_partial_key_backup(
            GUARDIAN_2_ID, identity_auxiliary_decrypt
        )
        verification2 = GUARDIAN_2.verify_election_partial_key_backup(
            GUARDIAN_1_ID, identity_auxiliary_decrypt
        )

        # Act
        mediator.receive_election_partial_key_verification(verification1)

        # Assert
        self.assertFalse(mediator.all_election_partial_key_verifications_received())
        self.assertFalse(mediator.all_election_partial_key_backups_verified())
        self.assertIsNone(mediator.publish_joint_key())

        # Act
        mediator.receive_election_partial_key_verification(verification2)
        joint_key = mediator.publish_joint_key()

        # Assert
        self.assertTrue(mediator.all_election_partial_key_verifications_received())
        self.assertTrue(mediator.all_election_partial_key_backups_verified())
        self.assertIsNotNone(joint_key)

    def test_partial_key_backup_verification_failure(self):
        """
        In this case, the recipient guardian does not correctly verify the sent key backup.
        This failed verificaton requires the sender create a challenge and a new verifier aka another guardian must verify this challenge.
        """
        # Arrange
        mediator = KeyCeremonyMediator(CEREMONY_DETAILS)
        mediator.confirm_presence_of_guardian(GUARDIAN_1.share_public_keys())
        mediator.confirm_presence_of_guardian(GUARDIAN_2.share_public_keys())
        mediator.receive_election_partial_key_backup(
            GUARDIAN_1.share_election_partial_key_backup(GUARDIAN_2_ID)
        )
        mediator.receive_election_partial_key_backup(
            GUARDIAN_2.share_election_partial_key_backup(GUARDIAN_1_ID)
        )
        GUARDIAN_1.save_election_partial_key_backup(
            mediator.share_election_partial_key_backups_to_guardian(GUARDIAN_1_ID)[0]
        )
        GUARDIAN_2.save_election_partial_key_backup(
            mediator.share_election_partial_key_backups_to_guardian(GUARDIAN_2_ID)[0]
        )
        verification1 = GUARDIAN_1.verify_election_partial_key_backup(
            GUARDIAN_2_ID, identity_auxiliary_decrypt
        )
        verification2 = GUARDIAN_2.verify_election_partial_key_backup(
            GUARDIAN_1_ID, identity_auxiliary_decrypt
        )

        # Act
        failed_verification2 = ElectionPartialKeyVerification(
            verification2.owner_id,
            verification2.designated_id,
            verification2.verifier_id,
            False,
        )
        mediator.receive_election_partial_key_verification(verification1)
        mediator.receive_election_partial_key_verification(failed_verification2)
        failed_pairs = mediator.share_failed_partial_key_verifications()
        missing_challenges = mediator.share_missing_election_partial_key_challenges()

        # Assert
        self.assertTrue(mediator.all_election_partial_key_verifications_received())
        self.assertFalse(mediator.all_election_partial_key_backups_verified())
        self.assertIsNone(mediator.publish_joint_key())
        self.assertEqual(len(failed_pairs), 1)
        self.assertEqual(failed_pairs[0], GuardianPair(GUARDIAN_1_ID, GUARDIAN_2_ID))
        self.assertEqual(len(missing_challenges), 1)
        self.assertEqual(
            missing_challenges[0], GuardianPair(GUARDIAN_1_ID, GUARDIAN_2_ID)
        )

        # Act
        challenge = GUARDIAN_1.publish_election_backup_challenge(GUARDIAN_2_ID)
        mediator.receive_election_partial_key_challenge(challenge)
        no_missing_challenges = mediator.share_missing_election_partial_key_challenges()

        # Assert
        self.assertFalse(mediator.all_election_partial_key_backups_verified())
        self.assertEqual(len(no_missing_challenges), 0)

        # Act
        challenges = mediator.share_open_election_partial_key_challenges()
        challenge_verification = VERIFIER.verify_election_partial_key_challenge(
            challenges[0]
        )
        mediator.receive_election_partial_key_verification(challenge_verification)
        joint_key = mediator.publish_joint_key()

        # Assert
        self.assertEqual(len(challenges), 1)
        self.assertTrue(mediator.all_election_partial_key_backups_verified())
        self.assertIsNotNone(joint_key)
