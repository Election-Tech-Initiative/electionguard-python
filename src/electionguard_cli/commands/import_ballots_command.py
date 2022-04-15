from io import TextIOWrapper
from typing import List, Tuple
import click
from electionguard.ballot import BallotBoxState, SubmittedBallot

from electionguard.election_builder import ElectionBuilder
from electionguard.manifest import InternalManifest
from electionguard.scheduler import Scheduler
from electionguard.tally import CiphertextTally
from ..cli_models import BuildElectionResults, ImportBallotInputs
from ..e2e_steps import (
    DecryptStep,
    ImportBallotsInputRetrievalStep,
)


@click.command()
@click.option(
    "--guardian-count",
    prompt="Number of guardians",
    help="The number of guardians that will participate in the key ceremony and tally.",
    type=click.INT,
)
@click.option(
    "--quorum",
    prompt="Quorum",
    help="The minimum number of guardians required to show up to the tally.",
    type=click.INT,
)
@click.option(
    "--manifest",
    prompt="Manifest file",
    help="The location of an election manifest.",
    type=click.File(),
)
@click.option(
    "--ballots-dir",
    prompt="Ballots file",
    help="The location of a file that contains plaintext ballots.",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
def import_ballots(
    guardian_count: int, quorum: int, manifest: TextIOWrapper, ballots_dir: str
) -> None:
    """
    Imports ballots
    """

    # get user inputs
    election_inputs = ImportBallotsInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, ballots_dir
    )

    # perform election
    build_election_results = _make_election_results(election_inputs)
    (ciphertext_tally, spoiled_ballots) = _create_tally(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_tally(
        ciphertext_tally,
        spoiled_ballots,
        election_inputs.guardians,
        build_election_results,
    )
    click.echo(decrypt_results.plaintext_tally)


# todo: convert into a step
def _make_election_results(election_inputs: ImportBallotInputs) -> BuildElectionResults:
    election_builder = ElectionBuilder(
        election_inputs.guardian_count,
        election_inputs.quorum,
        election_inputs.manifest,
    )
    election_builder.set_public_key(election_inputs.context.elgamal_public_key)
    election_builder.set_commitment_hash(election_inputs.context.commitment_hash)
    internal_manifest = InternalManifest(election_inputs.manifest)
    return BuildElectionResults(internal_manifest, election_inputs.context)


# todo: make this into a step
def _create_tally(
    election_inputs: ImportBallotInputs, build_election_results: BuildElectionResults
) -> Tuple[CiphertextTally, List[SubmittedBallot]]:
    tally = CiphertextTally(
        "object_id",
        build_election_results.internal_manifest,
        build_election_results.context,
    )
    ballots = [(None, b) for b in election_inputs.submitted_ballots]
    with Scheduler() as scheduler:
        tally.batch_append(ballots, scheduler)

    spoiled_ballots = [
        b
        for b in election_inputs.submitted_ballots
        if b.state == BallotBoxState.SPOILED
    ]

    return (tally, spoiled_ballots)
