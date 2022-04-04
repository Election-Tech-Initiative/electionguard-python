import pprint
import click
from e2e_steps.e2e_step_base import E2eStepBase
from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox, get_ballots
from electionguard.type import BallotId
from electionguard_tools.factories.ballot_factory import BallotFactory
from electionguard.encrypt import EncryptionMediator
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.guardian import Guardian
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.manifest import InternalManifest, Manifest
from electionguard.utils import get_optional
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)
from typing import Callable, Dict, List, Union, Tuple, Optional
from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
    PlaintextBallot,
    SubmittedBallot,
)
from electionguard.tally import (
    PublishedCiphertextTally,
    tally_ballots,
    CiphertextTally,
    PlaintextTally,
)
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord

class KeyCeremonyStep(E2eStepBase):
    def run_key_ceremony(self, guardians: List[Guardian]) -> None:
        self.print_header("Performing key ceremony")
        mediator: KeyCeremonyMediator = KeyCeremonyMediator(
            "mediator_1", guardians[0].ceremony_details
        )

        # ROUND 1: Public Key Sharing
        # Announce
        for guardian in guardians:
            mediator.announce(guardian.share_key())

        # Share Keys
        for guardian in guardians:
            announced_keys = get_optional(mediator.share_announced())
            for key in announced_keys:
                if guardian.id is not key.owner_id:
                    guardian.save_guardian_key(key)

        if (not mediator.all_guardians_announced()):
            click.echo('all guardians failed to announce')
            return

        # ROUND 2: Election Partial Key Backup Sharing
        # Share Backups
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

        # Receive Backups
        for designated_guardian in guardians:
            backups = get_optional(mediator.share_backups(designated_guardian.id))
            for backup in backups:
                designated_guardian.save_election_partial_key_backup(backup)

        # ROUND 3: Verification of Backups
        # Verify Backups
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

        # FINAL: Publish Joint Key
        joint_key = mediator.publish_joint_key()
        self.print_value("Joint Key", joint_key.joint_public_key)
        return get_optional(joint_key)

