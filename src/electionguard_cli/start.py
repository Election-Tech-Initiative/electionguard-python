import click
from electionguard_cli.e2e import e2e
from electionguard_cli.hello import hello

@click.group()
def cli():
    pass

cli.add_command(hello)
cli.add_command(e2e)