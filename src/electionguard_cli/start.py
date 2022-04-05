import click
from electionguard_cli.commands import e2e, hello


@click.group()
def cli() -> None:
    pass


cli.add_command(hello)
cli.add_command(e2e)
