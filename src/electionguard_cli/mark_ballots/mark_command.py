from io import TextIOWrapper
import click


from .mark_ballots_election_builder_step import MarkBallotsElectionBuilderStep
from .mark_ballots_input_retrieval_step import MarkBallotsInputRetrievalStep
from .mark_ballots_publish_step import MarkBallotsPublishStep
from ..cli_steps import MarkBallotsStep


@click.command("mark-ballots")
@click.argument("num_ballots", type=click.INT)
@click.argument("ballot_style_id", type=click.STRING, required=False)
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
def MarkBallotsCommand(
    num_ballots: int,
    ballot_style_id: str,
    manifest: TextIOWrapper,
    context: TextIOWrapper,
    out_dir: str,
) -> None:
    """
    Marks ballots
    """

    election_inputs = MarkBallotsInputRetrievalStep().get_inputs(manifest, context)
    build_election_results = (
        MarkBallotsElectionBuilderStep().build_election_with_context(election_inputs)
    )
    marked_ballots = MarkBallotsStep().mark(
        build_election_results, num_ballots, ballot_style_id
    )
    MarkBallotsPublishStep().publish(marked_ballots, out_dir)
