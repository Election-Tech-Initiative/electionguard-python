import click
from .commands.e2e_command import e2e
from .commands.import_ballots_command import import_ballots


@click.group()
def cli() -> None:
    pass


cli.add_command(e2e)
cli.add_command(import_ballots)
