from io import TextIOWrapper
import click

from .encrypt_ballots_election_builder_step import EncryptBallotsElectionBuilderStep
from .encrypt_ballots_input_retrieval_step import EncryptBallotsInputRetrievalStep


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
def EncryptBallotsCommand(
    manifest: TextIOWrapper,
    context: TextIOWrapper,
    ballots_dir: str,
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
