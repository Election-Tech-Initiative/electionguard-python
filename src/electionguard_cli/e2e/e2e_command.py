from io import TextIOWrapper
import click

from ..cli_steps import (
    ElectionBuilderStep,
    DecryptStep,
    PrintResultsStep,
    TallyStep,
    KeyCeremonyStep,
)
from .e2e_input_retrieval_step import E2eInputRetrievalStep
from .submit_votes_step import SubmitVotesStep
from .e2e_publish_step import E2ePublishStep


@click.command("e2e")
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
    type=click.Path(
        exists=False,
        dir_okay=False,
        file_okay=True,
    ),
    default=None,
)
@click.option(
    "--output-keys",
    help="A directory for saving the private and public guardian keys (e.g. './guardian-keys')."
    + " If no value provided then no keys will be output.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
    default=None,
)
def E2eCommand(
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
    build_election_results = ElectionBuilderStep().build_election_with_key(
        election_inputs, joint_key
    )
    submit_results = SubmitVotesStep().submit_votes(
        election_inputs, build_election_results
    )
    (ciphertext_tally, spoiled_ballots) = TallyStep().get_from_ballot_store(
        build_election_results, submit_results.data_store
    )
    decrypt_results = DecryptStep().decrypt(
        ciphertext_tally,
        spoiled_ballots,
        election_inputs.guardians,
        build_election_results,
    )

    # print results
    PrintResultsStep().print_election_results(decrypt_results)

    # publish election record
    E2ePublishStep().export(
        election_inputs, build_election_results, submit_results, decrypt_results
    )
