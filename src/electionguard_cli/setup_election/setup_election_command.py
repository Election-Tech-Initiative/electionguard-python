import click


@click.command("setup")
def SetupElectionCommand() -> None:
    """
    This command runs an automated key ceremony and produces the files necessary to both encrypt ballots, decrypt an election, and produce an election record.
    """

    click.echo("Hello")
