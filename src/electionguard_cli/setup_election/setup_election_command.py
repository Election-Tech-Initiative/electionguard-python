from io import TextIOWrapper
import click

from .setup_election_builder_step import SetupElectionBuilderStep
from .output_setup_files_step import OutputSetupFilesStep
from ..cli_steps import KeyCeremonyStep
from .setup_input_retrieval_step import SetupInputRetrievalStep


@click.command("setup")
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
    "--url",
    help="An optional verification url for the election.",
    required=False,
    type=click.STRING,
    default=None,
    prompt=False,
)
@click.option(
    "--package-dir",
    prompt="Election Package Output Directory",
    help="The location of a directory into which will be placed the output files such as "
    + "context, constants, and guardian keys. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--keys-dir",
    prompt="Private guardian keys directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
def SetupElectionCommand(
    guardian_count: int,
    quorum: int,
    manifest: TextIOWrapper,
    url: str,
    package_dir: str,
    keys_dir: str,
) -> None:
    """
    This command runs an automated key ceremony and produces the files
    necessary to encrypt ballots, decrypt an election, and produce an election record.
    """

    setup_inputs = SetupInputRetrievalStep().get_inputs(
        guardian_count, quorum, manifest, url
    )
    joint_key = KeyCeremonyStep().run_key_ceremony(setup_inputs.guardians)
    build_election_results = SetupElectionBuilderStep().build_election_for_setup(
        setup_inputs, joint_key
    )
    OutputSetupFilesStep().output(
        setup_inputs, build_election_results, package_dir, keys_dir
    )
