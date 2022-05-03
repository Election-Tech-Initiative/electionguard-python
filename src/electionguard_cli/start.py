import click

from .setup_election.setup_election_command import SetupElectionCommand
from .e2e.e2e_command import E2eCommand
from .import_ballots.import_ballots_command import ImportBallotsCommand


@click.group()
def cli() -> None:
    pass


cli.add_command(E2eCommand)
cli.add_command(ImportBallotsCommand)
cli.add_command(SetupElectionCommand)
