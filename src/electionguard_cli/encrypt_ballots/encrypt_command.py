import click


@click.command("encrypt-ballots")
@click.option(
    "--ballots-dir",
    prompt="Ballots file",
    help="The location of a file that contains plaintext ballots.",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True),
)
def EncryptBallotsCommand(
    ballots_dir: str,
) -> None:
    """
    Encrypt ballots, but does not submit them
    """

    click.echo("Ready to encrypt ballots to " + ballots_dir)
