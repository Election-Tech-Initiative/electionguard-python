import click
from electionguard_cli.commands.e2e_command import e2e
from electionguard_cli.commands.import_ballots_command import import_ballots


@click.group()
def cli() -> None:
    pass


cli.add_command(e2e)
cli.add_command(import_ballots)
