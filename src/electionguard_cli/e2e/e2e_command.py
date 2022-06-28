from io import TextIOWrapper
import click


from ..cli_steps import (
    DecryptStep,
    PrintResultsStep,
    TallyStep,
    KeyCeremonyStep,
    EncryptVotesStep,
)
from .e2e_input_retrieval_step import E2eInputRetrievalStep
from .submit_votes_step import SubmitVotesStep
from .e2e_publish_step import E2ePublishStep
from .e2e_election_builder_step import E2eElectionBuilderStep


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
    prompt="Ballots file or directory",
    help="The location of a file or directory that contains plaintext ballots.",
    type=click.Path(exists=True, dir_okay=True, file_okay=True),
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
    "--url",
    help="An optional verification url for the election.",
    required=False,
    type=click.STRING,
    default=None,
    prompt=False,
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
    ballots: str,
    spoil_id: str,
    url: str,
    output_record: str,
    output_keys: str,
) -> None:
    """Runs through an end-to-end election."""

    # get user inputs
    election_inputs = E2eInputRetrievalStep().get_inputs(
        guardian_count,
        quorum,
        manifest,
        ballots,
        spoil_id,
        output_record,
        output_keys,
        url,
    )

    # perform election
    joint_key = KeyCeremonyStep().run_key_ceremony(election_inputs.guardians)
    build_election_results = E2eElectionBuilderStep().build_election_with_key(
        election_inputs, joint_key
    )
    encrypt_results = EncryptVotesStep().encrypt(
        election_inputs.ballots, build_election_results
    )
    data_store = SubmitVotesStep().submit(
        election_inputs, build_election_results, encrypt_results
    )
    (ciphertext_tally, spoiled_ballots) = TallyStep().get_from_ballot_store(
        build_election_results, data_store
    )
    decrypt_results = DecryptStep().decrypt(
        ciphertext_tally,
        spoiled_ballots,
        election_inputs.guardians,
        build_election_results,
        election_inputs.manifest,
    )

    # print results
    PrintResultsStep().print_election_results(decrypt_results, election_inputs.manifest)

    # publish election record
    E2ePublishStep().export(
        election_inputs,
        build_election_results,
        encrypt_results,
        decrypt_results,
        data_store,
    )
