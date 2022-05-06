import click

from .cli_setup_election.setup_election_command import SetupElectionCommand
from .cli_e2e.e2e_command import E2eCommand
from .cli_import_ballots.import_ballots_command import ImportBallotsCommand
from .cli_encrypt_ballots.encrypt_command import EncryptBallotsCommand


@click.group()
def cli() -> None:
    pass


cli.add_command(E2eCommand)
cli.add_command(SetupElectionCommand)
cli.add_command(EncryptBallotsCommand)
cli.add_command(ImportBallotsCommand)
