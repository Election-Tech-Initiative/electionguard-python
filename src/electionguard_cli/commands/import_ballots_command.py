import click


@click.command()
def import_ballots() -> None:
    """
    Imports ballots
    """
    click.echo("world")
