import click
from .commands import e2e, import_ballots


@click.group()
def cli() -> None:
    pass


cli.add_command(e2e)
cli.add_command(import_ballots)
