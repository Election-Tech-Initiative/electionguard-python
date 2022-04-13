from io import TextIOWrapper
import click
from ..e2e_steps import (
    ElectionBuilderStep,
    KeyCeremonyStep,
    SubmitVotesStep,
    DecryptStep,
    PrintResultsStep,
    E2eInputRetrievalStep,
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
    "--output-file",
    help="A file name for saving an output election record (e.g. './election.zip')."
    + " If no value provided then an election record will not be generated.",
    type=click.Path(exists=False),
    default=None,
)
def e2e(
    guardian_count: int,
    quorum: int,
    manifest: TextIOWrapper,
    ballots: TextIOWrapper,
    spoil_id: str,
    output_file: str,
) -> None:
    """Runs through an end-to-end election."""

    # get user inputs
    election_inputs = E2eInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, ballots, spoil_id, output_file
    )

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs)
    build_election_results = ElectionBuilderStep().build_election(
        election_inputs, joint_key
    )
    submit_results = SubmitVotesStep().submit_votes(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_tally(
        submit_results.data_store, election_inputs.guardians, build_election_results
    )

    # print results
    PrintResultsStep().print_election_results(election_inputs, decrypt_results)

    # publish election record
    ElectionRecordStep().run(
        election_inputs, build_election_results, submit_results, decrypt_results
    )
