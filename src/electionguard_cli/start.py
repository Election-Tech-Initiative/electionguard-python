import click

from .setup_election.setup_election_command import SetupElectionCommand
from .e2e.e2e_command import E2eCommand
from .import_ballots.import_ballots_command import ImportBallotsCommand
from .encrypt_ballots.encrypt_command import EncryptBallotsCommand
from .mark_ballots.mark_command import MarkBallotsCommand
from .submit_ballots.submit_command import SubmitBallotsCommand


@click.group()
def cli() -> None:
    pass


cli.add_command(E2eCommand)
cli.add_command(SetupElectionCommand)
cli.add_command(MarkBallotsCommand)
cli.add_command(EncryptBallotsCommand)
cli.add_command(SubmitBallotsCommand)
cli.add_command(ImportBallotsCommand)
