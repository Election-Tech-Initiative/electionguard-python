from io import TextIOWrapper
import click
from electionguard.ballot import BallotBoxState
from electionguard.ballot_box import BallotBox

from electionguard.data_store import DataStore
from electionguard_cli.cli_models.e2e_build_election_results import BuildElectionResults
from electionguard_cli.cli_models.e2e_inputs import ImportBallotInputs
from ..e2e_steps import (
    ElectionBuilderStep,
    KeyCeremonyStep,
)
from ..e2e_steps import (
    DecryptStep,
)
from electionguard_cli.e2e_steps.input_retrieval_step import (
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
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = ElectionBuilderStep().build_election(
        election_inputs, joint_key
    )
    ballot_store = _read_ballots(election_inputs, build_election_results)
    decrypt_results = DecryptStep().decrypt_tally(
        ballot_store, election_inputs.guardians, build_election_results
    )
    # click.echo(decrypt_results.plaintext_tally)


def _read_ballots(
    election_inputs: ImportBallotInputs, build_election_results: BuildElectionResults
) -> DataStore:
    ballot_store: DataStore = DataStore()
    ballot_box = BallotBox(
        build_election_results.internal_manifest,
        build_election_results.context,
        ballot_store,
    )
    for ballot in election_inputs.submitted_ballots:
        spoil = ballot.state == BallotBoxState.SPOILED
        if spoil:
            ballot_box.spoil(ballot)
        else:
            ballot_box.cast(ballot)

        click.echo(f"Submitted Ballot Id: {ballot.object_id} state: {ballot.state}")
    return ballot_store
