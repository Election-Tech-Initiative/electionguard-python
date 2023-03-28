import click
from typing import Any, Optional

VERIFICATION_URL_NAME = "verification_url"

def print_header(text: str, header_color="green") -> None:
    click.echo("")
    click.secho(f"{'-'*40}", fg=header_color)
    click.echo(text, fg=header_color)
    click.echo(f"{'-'*40}", header_color)

def print_message(text: str, color="white", underlined=False, bolded=False) -> None:
    click.secho(f"{text}", fg=color, underline=underlined, bold=bolded)

def print_warning(text: str, warning_color="bright_red") -> None:
    click.secho(f"WARNING: {text}", fg=warning_color, bold=True)

def print_error(text: str, error_color="bright_red"):
    click.secho(f"Error: {text}", fg=error_color, bold=True, italic=True)

def print_value(name: str, value: Any, value_color="yellow") -> None:
    click.echo(click.style(name + ": ") + click.style(value, fg=self.value_color))

def print_section(text: Optional[str], section_color="bright-white") -> None:
    click.echo("")
    click.secho(text, fg=section_color, bold=True)

def cleanup() -> None:
    click.clear()