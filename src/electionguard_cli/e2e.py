import click
from e2e_steps.key_ceremony_step import KeyCeremonyStep
from electionguard.data_store import DataStore
from electionguard.ballot_box import BallotBox, get_ballots
from electionguard.type import BallotId
from electionguard_tools.factories.ballot_factory import BallotFactory
from electionguard.encrypt import EncryptionMediator
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.guardian import Guardian
from electionguard.manifest import InternalManifest, Manifest
from electionguard.utils import get_optional
from electionguard_tools.factories.election_factory import (
    ElectionFactory,
)
from typing import Dict, List, Tuple, Optional
from electionguard.ballot import (
    BallotBoxState,
    CiphertextBallot,
)
from electionguard.tally import (
    tally_ballots,
    PlaintextTally,
)
from electionguard.decryption_mediator import DecryptionMediator
from electionguard.election_polynomial import LagrangeCoefficientsRecord

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

    def print_manifest(manifest: Manifest) -> None:
        manifest_name = manifest.name.text[0].value
        print_value("Name", manifest_name)
        print_value("Scope", manifest.election_scope_id)
        print_value("Geopolitical Units", len(manifest.geopolitical_units))
        print_value("Parties", len(manifest.parties))
        print_value("Candidates", len(manifest.candidates))
        print_value("Contests", len(manifest.contests))
        print_value("Ballot Styles", len(manifest.ballot_styles))
        print_value("Guardians", guardian_count)
        print_value("Quorum", quorum)

    def get_manifest() -> Optional[Manifest]:
        # todo: get manifest from params
        print_header('Retrieving manifest')
        manifest = ElectionFactory().get_simple_manifest_from_file()
        if (not manifest.is_valid()):
            click.echo('manifest file is invalid')
            return None
        print_manifest(manifest)
        return manifest

    def get_guardians(number_of_guardians: int) -> List[Guardian]:
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
        return guardians

    def build_election(joint_key, guardian_count, quorum, manifest) -> Tuple[InternalManifest, CiphertextElectionContext]:
        print_header("Building election")

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

    def encrypt_votes() -> List[CiphertextBallot]:
        print_header("Encrypting votes")
        # Get Ballots
        # todo: parameterize the plaintext ballot file
        plaintext_ballots = BallotFactory().get_simple_ballots_from_file()
        print_value("Loaded ballots", len(plaintext_ballots))

        # Configure the Encryption Device
        device = ElectionFactory.get_encryption_device()
        encrypter = EncryptionMediator(
            internal_manifest, context, device
        )
        click.echo(f"Ready to encrypt at location: {device.location}")

        ciphertext_ballots: List[CiphertextBallot] = []
        # Encrypt the Ballots
        for plaintext_ballot in plaintext_ballots:
            encrypted_ballot = encrypter.encrypt(plaintext_ballot)
            click.echo(f"Encrypting ballot: {plaintext_ballot.object_id}")
            ciphertext_ballots.append(get_optional(encrypted_ballot))
        return ciphertext_ballots

    def cast_and_spoil(ballot_store: DataStore, internal_manifest: InternalManifest, context: CiphertextElectionContext, ciphertext_ballots: List[CiphertextBallot]) -> None:
        # Configure the Ballot Box
        ballot_box = BallotBox(
            internal_manifest, context, ballot_store
        )

        # spoil the 1st ballot, cast the rest
        first = True
        for ballot in ciphertext_ballots:
            if first:
                submitted_ballot = ballot_box.spoil(ballot)
            else:
                submitted_ballot = ballot_box.cast(ballot)
            first = False

            click.echo(f"Submitted Ballot Id: {ballot.object_id} state: {get_optional(submitted_ballot).state}")

    def decrypt_tally(ballot_store: DataStore, guardians: List[Guardian], ciphertext_ballots: List[CiphertextBallot]) -> Tuple[CiphertextBallot, Dict[BallotId, PlaintextTally]]:
        print_header("Decrypting tally")
        ciphertext_tally = get_optional(
            tally_ballots(ballot_store, internal_manifest, context)
        )
        submitted_ballots = get_ballots(ballot_store, BallotBoxState.SPOILED)
        click.echo("Decrypting tally")
        print_value("Cast ballots", ciphertext_tally.cast())
        print_value("Spoiled ballots", ciphertext_tally.cast())
        print_value("Total ballots", len(ciphertext_tally))

        # Configure the Decryption
        submitted_ballots_list = list(submitted_ballots.values())
        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            context,
        )

        # Announce each guardian as present
        count = 0
        for guardian in guardians:
            guardian_key = guardian.share_key()
            tally_share = guardian.compute_tally_share(
                ciphertext_tally, context
            )
            ballot_shares = guardian.compute_ballot_shares(
                submitted_ballots_list, context
            )
            decryption_mediator.announce(
                guardian_key, get_optional(tally_share), ballot_shares
            )
            count += 1
            click.echo(f"Guardian Present: {guardian.id}")

        lagrange_coefficients = LagrangeCoefficientsRecord(
            decryption_mediator.get_lagrange_coefficients()
        )

        # Get the plaintext Tally
        plaintext_tally = get_optional(
            decryption_mediator.get_plaintext_tally(ciphertext_tally)
        )

        # Get the plaintext Spoiled Ballots
        plaintext_spoiled_ballots = get_optional(
            decryption_mediator.get_plaintext_ballots(submitted_ballots_list)
        )

        return (plaintext_tally, plaintext_spoiled_ballots)

    def print_tally(plaintext_tally):
        print_header('Decrypted tally')
        for contest in plaintext_tally.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                click.echo(f"  Selection '{selection.object_id}' received: {selection.tally} votes")

    def print_spoiled_ballot(plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]) -> None:
        ballot_id = list(plaintext_spoiled_ballots)[0]
        print_header(f"Spoiled ballot '{ballot_id}'")
        spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
        for contest in spoiled_ballot.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                click.echo(f"  Selection '{selection.object_id}' received {selection.tally} vote")

    manifest: Manifest = get_manifest()
    if (manifest is None): return
    guardians = get_guardians(guardian_count)
    joint_key = KeyCeremonyStep().run_key_ceremony(guardians)
    internal_manifest, context = build_election(joint_key, guardian_count, quorum, manifest)
    ciphertext_ballots = encrypt_votes()
    ballot_store = DataStore()
    cast_and_spoil(ballot_store, internal_manifest, context, ciphertext_ballots)
    (tally, spoiled_ballots) = decrypt_tally(ballot_store, guardians, ciphertext_ballots)
    print_tally(tally)
    print_spoiled_ballot(spoiled_ballots)
