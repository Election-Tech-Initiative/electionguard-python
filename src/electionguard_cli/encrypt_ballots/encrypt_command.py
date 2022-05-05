from io import TextIOWrapper
import click


from .encrypt_ballots_election_builder_step import EncryptBallotsElectionBuilderStep
from .encrypt_ballots_input_retrieval_step import EncryptBallotsInputRetrievalStep
from .encrypt_ballots_publish_step import EncryptBallotsPublishStep
from ..cli_steps import EncryptVotesStep


@click.command("encrypt-ballots")
@click.option(
    "--manifest",
    prompt="Manifest file",
    help="The location of an election manifest.",
    type=click.File(),
)
@click.option(
    "--context",
    prompt="Context file",
    help="The location of an election context.",
    type=click.File(),
)
@click.option(
    "--ballots-dir",
    prompt="Ballots file",
    help="The location of a file that contains plaintext ballots.",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--out-dir",
    help="A directory for saving encrypted ballots and encryption device to.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def EncryptBallotsCommand(
    manifest: TextIOWrapper, context: TextIOWrapper, ballots_dir: str, out_dir: str
) -> None:
    """
    Encrypt ballots, but does not submit them
    """

    election_inputs = EncryptBallotsInputRetrievalStep().get_inputs(
        manifest, context, ballots_dir
    )
    build_election_results = (
        EncryptBallotsElectionBuilderStep().build_election_with_context(election_inputs)
    )
    encrypt_results = EncryptVotesStep().encrypt(
        election_inputs.plaintext_ballots, build_election_results
    )
    EncryptBallotsPublishStep().publish(encrypt_results, out_dir)
