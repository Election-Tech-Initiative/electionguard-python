from typing import List
from unittest import TestCase

from electionguard.guardian import Guardian
from electionguard.key_ceremony_mediator import KeyCeremonyMediator


class TestEndToEndElection(TestCase):
    """
    A full happy path of the end to end election using the mediator
    """

    NUMBER_OF_GUARDIANS = 5
    QUORUM = 3

    mediator: KeyCeremonyMediator
    guardians: List[Guardian] = []

    def test_end_to_end_election(self) -> None:
        self.step_1_key_ceremony()
        self.step_2_voting()
        self.step_3_ballot_box()

    def step_1_key_ceremony(self) -> None:
        # Setup Guardians
        for i in range(self.NUMBER_OF_GUARDIANS):
            self.guardians.append(
                Guardian("guardian_" + str(i), i, self.NUMBER_OF_GUARDIANS, self.QUORUM)
            )

        # Setup Mediator
        self.mediator = KeyCeremonyMediator(self.guardians[0].ceremony_details)

        # Attendance (Public Key Share)
        for guardian in self.guardians:
            self.mediator.confirm_presence_of_guardian(guardian.share_public_keys())

        self.assertTrue(self.mediator.all_guardians_in_attendance())

        # Partial Key Backup Generation
        for guardian in self.guardians:
            guardian.generate_election_partial_key_backups()

        # Share Partial Key Backup
        for sender_guardian in self.guardians:
            for recipient_guardian in self.guardians:
                if sender_guardian.object_id != recipient_guardian.object_id:
                    backup = sender_guardian.share_election_partial_key_backup(
                        recipient_guardian.object_id
                    )
                    if backup is not None:
                        self.mediator.receive_election_partial_key_backup(backup)

        self.assertTrue(self.mediator.all_election_partial_key_backups_available())

        for recipient_guardian in self.guardians:
            backups = self.mediator.share_election_partial_key_backups_to_guardian(
                recipient_guardian.object_id
            )
            for backup in backups:
                recipient_guardian.save_election_partial_key_backup(backup)

        # Verification
        for recipient_guardian in self.guardians:
            for sender_guardian in self.guardians:
                if sender_guardian.object_id != recipient_guardian.object_id:
                    verification = recipient_guardian.verify_election_partial_key_backup(
                        sender_guardian.object_id
                    )
                    if verification is not None:
                        self.mediator.receive_election_partial_key_verification(
                            verification
                        )

        self.assertTrue(self.mediator.all_election_partial_key_verifications_received())
        self.assertTrue(self.mediator.all_election_partial_key_backups_verified())

        # Joint Key
        joint_key = self.mediator.publish_joint_key()
        self.assertIsNotNone(joint_key)

    def step_2_voting(self) -> None:
        pass

    def step_3_ballot_box(self) -> None:
        pass
