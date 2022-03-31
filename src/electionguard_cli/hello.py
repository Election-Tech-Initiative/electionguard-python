import click

@click.command()
def hello():
    """Simply prints world. This is just an example of an arbitrary second command and should be deleted as soon as there is a real command other than e2e."""
    click.echo('world')
