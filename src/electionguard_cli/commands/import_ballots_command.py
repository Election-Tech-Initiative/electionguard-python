from io import TextIOWrapper
import click

from ..steps.shared import DecryptStep, PrintResultsStep, ElectionBuilderStep, TallyStep
from ..steps.import_ballots import (
    ImportBallotsInputRetrievalStep,
)


@click.command()
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
    "--guardian-keys",
    prompt="Guardian keys file",
    help="The location of a json file with all guardians's private key data. "
    + "This corresponds to the output-keys parameter of the e2e command.",
    type=click.Path(exists=True, dir_okay=False, file_okay=True, resolve_path=True),
)
def import_ballots(
    manifest: TextIOWrapper,
    context: TextIOWrapper,
    ballots_dir: str,
    guardian_keys: str,
) -> None:
    """
    Imports ballots
    """

    # get user inputs
    election_inputs = ImportBallotsInputRetrievalStep().get_inputs(
        manifest, context, ballots_dir, guardian_keys
    )

    # perform election
    build_election_results = ElectionBuilderStep().build_election_with_context(
        election_inputs
    )
    (ciphertext_tally, spoiled_ballots) = TallyStep().get_from_ballots(
        build_election_results, election_inputs.submitted_ballots
    )
    decrypt_results = DecryptStep().decrypt(
        ciphertext_tally,
        spoiled_ballots,
        election_inputs.guardians,
        build_election_results,
    )

    # print results
    PrintResultsStep().print_election_results(decrypt_results)
