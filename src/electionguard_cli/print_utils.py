import click

def Echo(output: str):
    click.echo(output)

def Secho(text: str, fg=None, bg=None, bold=None, dim=None, underline=None, blink=None, reverse=None, reset=True):
    click.secho(text, fg, bg, bold, dim, underline, blink, reverse, reset)