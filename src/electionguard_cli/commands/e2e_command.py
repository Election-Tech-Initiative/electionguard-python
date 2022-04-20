from io import TextIOWrapper
import click

from ..steps.e2e import (
    E2eInputRetrievalStep,
    KeyCeremonyStep,
    SubmitVotesStep,
)
from ..steps.shared import (
    ElectionBuilderStep,
    DecryptStep,
    PrintResultsStep,
    ElectionRecordStep,
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
    "--ballots",
    prompt="Ballots file",
    help="The location of a file that contains plaintext ballots.",
    type=click.File(),
)
@click.option(
    "--spoil-id",
    prompt="Object-id of ballot to spoil",
    help="The object-id of a ballot within the ballots file to spoil.",
    type=click.STRING,
    default=None,
    prompt_required=False,
)
@click.option(
    "--output-record",
    help="A file name for saving an output election record (e.g. './election.zip')."
    + " If no value provided then an election record will not be generated.",
    type=click.Path(exists=False),
    default=None,
)
@click.option(
    "--output-keys",
    help="A file name for saving the private and public guardian keys (e.g. './guardian-keys.json')."
    + " If no value provided then no keys will be output.",
    type=click.Path(exists=False),
    default=None,
)
def e2e(
    guardian_count: int,
    quorum: int,
    manifest: TextIOWrapper,
    ballots: TextIOWrapper,
    spoil_id: str,
    output_record: str,
    output_keys: str,
) -> None:
    """Runs through an end-to-end election."""

    # get user inputs
    election_inputs = E2eInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, ballots, spoil_id, output_record, output_keys
    )

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = ElectionBuilderStep().build_election(
        election_inputs, joint_key
    )
    submit_results = SubmitVotesStep().submit_votes(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_ballot_store(
        submit_results.data_store, election_inputs.guardians, build_election_results
    )

    # print results
    PrintResultsStep().print_election_results(decrypt_results)

    # publish election record
    ElectionRecordStep().run(
        election_inputs, build_election_results, submit_results, decrypt_results
    )
