from typing import List

from electionguard.key_ceremony import (
    CeremonyDetails,
    ElectionJointKey,
    ElectionPublicKey,
)
from electionguard.guardian import Guardian
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.utils import get_optional

from ..cli_models.e2e_inputs import E2eInputs
from .e2e_step_base import E2eStepBase


class KeyCeremonyStep(E2eStepBase):
    """Responsible for running a key ceremony and producing an elgamal public key given a list of guardians."""

    def __announce_guardians(
        self, mediator: KeyCeremonyMediator, guardians: List[Guardian]
    ) -> List[ElectionPublicKey]:
        for guardian in guardians:
            mediator.announce(guardian.share_key())
        return get_optional(mediator.share_announced())

    def __get_mediator(self, ceremony_details: CeremonyDetails) -> KeyCeremonyMediator:
        mediator: KeyCeremonyMediator = KeyCeremonyMediator(
            "mediator_1", ceremony_details
        )
        return mediator

    def __share_keys(
        self, announced_keys: List[ElectionPublicKey], guardians: List[Guardian]
    ) -> None:
        for guardian in guardians:
            for key in announced_keys:
                if guardian.id is not key.owner_id:
                    guardian.save_guardian_key(key)

    def __share_backups(
        self, mediator: KeyCeremonyMediator, guardians: List[Guardian]
    ) -> None:
        for sending_guardian in guardians:
            sending_guardian.generate_election_partial_key_backups()
            backups = []
            for designated_guardian in guardians:
                if designated_guardian.id != sending_guardian.id:
                    backups.append(
                        get_optional(
                            sending_guardian.share_election_partial_key_backup(
                                designated_guardian.id
                            )
                        )
                    )
            mediator.receive_backups(backups)

    def __receive_backups(
        self, mediator: KeyCeremonyMediator, guardians: List[Guardian]
    ) -> None:
        for designated_guardian in guardians:
            backups = get_optional(mediator.share_backups(designated_guardian.id))
            for backup in backups:
                designated_guardian.save_election_partial_key_backup(backup)

    def __verify_backups(
        self, mediator: KeyCeremonyMediator, guardians: List[Guardian]
    ) -> None:
        for designated_guardian in guardians:
            verifications = []
            for backup_owner in guardians:
                if designated_guardian.id is not backup_owner.id:
                    verification = (
                        designated_guardian.verify_election_partial_key_backup(
                            backup_owner.id
                        )
                    )
                    verifications.append(get_optional(verification))
            mediator.receive_backup_verifications(verifications)

    def run_key_ceremony(self, election_inputs: E2eInputs) -> ElectionJointKey:
        self.print_header("Performing key ceremony")

        guardians = election_inputs.guardians
        mediator: KeyCeremonyMediator = self.__get_mediator(
            guardians[0].ceremony_details
        )
        announced_keys = self.__announce_guardians(mediator, guardians)
        self.__share_keys(announced_keys, guardians)
        if not mediator.all_guardians_announced():
            raise ValueError("All guardians failed to announce successfully")
        self.__share_backups(mediator, guardians)
        self.__receive_backups(mediator, guardians)
        self.__verify_backups(mediator, guardians)
        joint_key = mediator.publish_joint_key()

        self.print_value("Joint Key", get_optional(joint_key).joint_public_key)
        return get_optional(joint_key)
