from typing import List

from electionguard.guardian import Guardian
from electionguard.key_ceremony import CeremonyDetails, ElectionPartialKeyVerification
from electionguard.key_ceremony_mediator import GuardianPair, KeyCeremonyMediator

from electionguard_tools.helpers.identity_encrypt import (
    identity_auxiliary_decrypt,
    identity_auxiliary_encrypt,
)


class KeyCeremonyOrchestrator:
    """Helper to assist in the key ceremony particularly for testing"""

    @staticmethod
    def create_guardians(ceremony_details: CeremonyDetails) -> List[Guardian]:
        return [
            Guardian(
                "guardian_" + str(i + 1),
                i + 1,
                ceremony_details.number_of_guardians,
                ceremony_details.quorum,
            )
            for i in range(ceremony_details.number_of_guardians)
        ]

    @staticmethod
    def perform_full_ceremony(guardians: List[Guardian], mediator: KeyCeremonyMediator):
        """Perform full key ceremony so joint election key is ready for publish"""

        KeyCeremonyOrchestrator.perform_round_1(guardians, mediator)
        KeyCeremonyOrchestrator.perform_round_2(guardians, mediator)
        KeyCeremonyOrchestrator.perform_round_3(guardians, mediator)

    @staticmethod
    def perform_round_1(
        guardians: List[Guardian], mediator: KeyCeremonyMediator
    ) -> None:
        """Perform Round 1 including announcing guardians and sharing public keys"""

        for guardian in guardians:
            mediator.announce(guardian.share_public_keys())

        for guardian in guardians:
            other_guardian_keys = mediator.share_announced(guardian.id)
            for guardian_public_keys in other_guardian_keys:
                guardian.save_guardian_public_keys(guardian_public_keys)

    @staticmethod
    def perform_round_2(
        guardians: List[Guardian], mediator: KeyCeremonyMediator
    ) -> None:
        """Perform Round 2 including generating backups and sharing backups"""

        for guardian in guardians:
            guardian.generate_election_partial_key_backups(identity_auxiliary_encrypt)
            mediator.receive_backups(guardian.share_election_partial_key_backups())

        for guardian in guardians:
            backups = mediator.share_backups(guardian.id)
            for backup in backups:
                guardian.save_election_partial_key_backup(backup)

    @staticmethod
    def perform_round_3(guardians: List[Guardian], mediator: KeyCeremonyMediator):
        """Perform Round 3 including verifying backups"""

        for guardian in guardians:
            for other_guardian in guardians:
                verifications = []
                if guardian.id is not other_guardian.id:
                    verifications.append(
                        guardian.verify_election_partial_key_backup(
                            other_guardian.id, identity_auxiliary_decrypt
                        )
                    )
                mediator.receive_backup_verifications(verifications)

    @staticmethod
    def fail_round_3(
        guardians: List[Guardian], mediator: KeyCeremonyMediator
    ) -> GuardianPair:
        """Perform Round 3 including verifying backups but fail a single backup"""

        failing_guardian_pair = GuardianPair(guardians[0].id, guardians[1].id)

        for guardian in guardians:
            for other_guardian in guardians:
                verifications = []
                if guardian.id is not other_guardian.id:
                    verification = guardian.verify_election_partial_key_backup(
                        other_guardian.id
                    )
                    if (
                        verification.owner_id is failing_guardian_pair.owner_id
                        and verification.designated_id
                        is failing_guardian_pair.designated_id
                    ):
                        verification = ElectionPartialKeyVerification(
                            failing_guardian_pair.owner_id,
                            failing_guardian_pair.designated_id,
                            failing_guardian_pair.designated_id,
                            False,
                        )
                    verifications.append(verification)
                mediator.receive_backup_verifications(verifications)

        return failing_guardian_pair
