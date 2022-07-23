import click
from typing import Any

def print_header_utils(text: str, header_color="green"):
    click.echo("")
    click.secho(f"{'-'*40}", fg=header_color)
    click.echo(text, fg=header_color)
    click.echo(f"{'-'*40}", header_color)

def print_message_utils(text: str, underlined=False):
    click.secho(f"{text}", fg="white", underline=underlined)

def print_warning_utils(text: str, warning_color="bright_red") -> None:
    click.secho(f"WARNING: {text}", fg=warning_color, bold=True)

def print_error_utils(text: str, error_color="bright_red"):
    click.secho(f"Error: {text}", fg=error_color, bold=True, italic=True)

def print_value_utils(text: str, val: Any):
    click.echo(click.style(text + ": ") + click.style(val, fg="yellow"))

def print_text_utils(text: Any):
    click.echo(text)

def cleanup_utits():
    click.clear()