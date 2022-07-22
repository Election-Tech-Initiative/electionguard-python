import click

def print_header(text: str, header_color="green"):
    click.echo("")
    click.secho(f"{'-'*40}", fg=header_color)
    click.echo(text, fg=header_color)
    click.echo(f"{'-'*40}", header_color)

def print_message(text: str, underlined=False):
    click.secho(f"{text}", fg="white", underline=underlined)

def print_warning(text: str, warning_color="bright_red") -> None:
    click.secho(f"WARNING: {text}", fg=warning_color, bold=True)

def print_error(text: str, error_color="bright_red"):
    click.secho(f"Error: {text}", fg=error_color, bold=True, italic=True)

def cleanup():
    click.clear()