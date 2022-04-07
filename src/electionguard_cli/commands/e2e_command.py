from io import TextIOWrapper
import click
from ..e2e_steps import (
    ElectionBuilderStep,
    KeyCeremonyStep,
    SubmitVotesStep,
    DecryptStep,
    PrintResultsStep,
    InputRetrievalStep,
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
    "--output-path",
    help="An optional directory in which to place the output election record. If no value provied then an election record will not be generated.",
    type=click.Path(exists=True, file_okay=False, writable=True, dir_okay=True),
    default=None,
)
def e2e(
    guardian_count: int,
    quorum: int,
    manifest: TextIOWrapper,
    ballots: TextIOWrapper,
    spoil_id: str,
    output_path: str,
) -> None:
    """Runs through an end-to-end election."""

    # get user inputs
    election_inputs = InputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, ballots, spoil_id, output_path
    )

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs)
    build_election_results = ElectionBuilderStep().build_election(
        election_inputs, joint_key
    )
    ballot_store = SubmitVotesStep().submit_votes(
        election_inputs, build_election_results
    )
    decrypt_results = DecryptStep().decrypt_tally(
        ballot_store, election_inputs.guardians, build_election_results
    )

    # print results
    PrintResultsStep().print_election_results(election_inputs, decrypt_results)

    # publish election record
    ElectionRecordStep().run(election_inputs, build_election_results)
