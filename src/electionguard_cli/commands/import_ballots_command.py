from io import TextIOWrapper
from typing import List
import click
from electionguard.data_store import DataStore
from electionguard.guardian import Guardian
from electionguard.manifest import InternalManifest, Manifest
from electionguard_cli.cli_models import BuildElectionResults
from electionguard_cli.e2e_steps.election_builder_step import ElectionBuilderStep
from electionguard_cli.e2e_steps.input_retrieval_step import (
    ImportBallotsInputRetrievalStep,
)

from ..e2e_steps import (
    DecryptStep,
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

    # data_store: DataStore = DataStore()
    # # todo: read all files in ballots and add them to data_store

    # guardians: List[Guardian] = []
    # # todo: add guardians

    # ElectionBuilderStep().build_election()

    # build_election_results = BuildElectionResults(internal_manifest, context)
    # decrypt_results = DecryptStep().decrypt_tally(
    #     data_store, guardians, build_election_results
    # )
    # click.echo(decrypt_results.plaintext_tally)
