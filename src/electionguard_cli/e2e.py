import click
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

@click.command()
@click.option('--guardian-count', prompt='Number of guardians', help='The number of guardians that will participate in the key ceremony and tally.', type=click.INT)
@click.option('--quorum', prompt='Quorum', help='The minimum number of guardians required to show up to the tally.', type=click.INT)
def e2e(guardian_count, quorum):
    """Runs through an end-to-end election."""

    def print_header(s: str) -> None:
        click.secho(f"{'-'*40}", fg='green')
        click.secho(s, fg='green')
        click.secho(f"{'-'*40}", fg='green')

    def print_value(name: str, value: any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg='yellow'))

    def get_manifest() -> Optional[Manifest]:
        # todo: get manifest from params
        manifest = ElectionFactory().get_simple_manifest_from_file()
        if (not manifest.is_valid()):
            click.echo('manifest file is invalid')
            return None
        return manifest


    def print_manifest() -> None:
        manifest_name = manifest.name.text[0].value
        print_header('Election Summary')
        print_value("Name", manifest_name)
        print_value("Scope", manifest.election_scope_id)
        print_value("Geopolitical Units", len(manifest.geopolitical_units))
        print_value("Parties", len(manifest.parties))
        print_value("Candidates", len(manifest.candidates))
        print_value("Contests", len(manifest.contests))
        print_value("Ballot Styles", len(manifest.ballot_styles))
        print_value("Guardians", guardian_count)
        print_value("Quorum", quorum)

    def run_key_ceremony(manifest: Manifest, number_of_guardians: int, quorum: int) -> None:
        guardians: List[Guardian] = []
        for i in range(number_of_guardians):
            guardians.append(
                Guardian(
                    str(i + 1),
                    i + 1,
                    number_of_guardians,
                    quorum,
                )
            )
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
        print_value("Joint Key", joint_key)
        return get_optional(joint_key)

    def build_election(joint_key) -> Tuple[InternalManifest, CiphertextElectionContext]:
        # Build the Election
        election_builder = ElectionBuilder(
            guardian_count, quorum, manifest
        )
        election_builder.set_public_key(get_optional(joint_key).joint_public_key)
        election_builder.set_commitment_hash(
            get_optional(joint_key).commitment_hash
        )
        return get_optional(
            election_builder.build()
        )

    manifest: Manifest = get_manifest()
    if (manifest is None): return
    print_manifest()

    joint_key = run_key_ceremony(manifest, guardian_count, quorum)
    internal_manifest, context = build_election(joint_key)
