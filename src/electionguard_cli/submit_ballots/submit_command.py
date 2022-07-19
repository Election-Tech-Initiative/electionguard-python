from io import TextIOWrapper
import click


from .submit_ballots_election_builder_step import SubmitBallotsElectionBuilderStep
from .submit_ballots_input_retrieval_step import SubmitBallotsInputRetrievalStep
from .submit_ballots_publish_step import SubmitBallotsPublishStep
from ..cli_steps import SubmitBallotsStep


@click.command("submit-ballots")
@click.argument(
    "cast_ballots_dir",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.argument(
    "spoil_ballots_dir",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
    required=False,
)
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
    "--out-dir",
    help="A directory for saving plaintext ballots to.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def SubmitBallotsCommand(
    cast_ballots_dir: str,
    spoil_ballots_dir: str,
    manifest: TextIOWrapper,
    context: TextIOWrapper,
    out_dir: str,
) -> None:
    """
    Submits ballots
    """

    election_inputs = SubmitBallotsInputRetrievalStep().get_inputs(
        manifest, context, cast_ballots_dir, spoil_ballots_dir
    )
    build_election_results = (
        SubmitBallotsElectionBuilderStep().build_election_with_context(election_inputs)
    )
    submitted_ballots = SubmitBallotsStep().submit(
        build_election_results,
        election_inputs.cast_ballots,
        election_inputs.spoil_ballots,
    )
    SubmitBallotsPublishStep().publish(submitted_ballots, out_dir)
