from typing import Any, Optional
#import click
from print_utils import *


class CliStepBase:
    """
    Responsible for providing common functionality to the individual steps within an end-to-end election command
    from the CLI.
    """

    header_color = "green"
    value_color = "yellow"
    warning_color = "bright_red"
    section_color = "bright_white"
    VERIFICATION_URL_NAME = "verification_url"

    def print_header(self, s: str) -> None:
        Echo("")
        Secho(f"{'-'*40}", fg=self.header_color)
        Secho(s, fg=self.header_color)
        Secho(f"{'-'*40}", self.header_color)

    def print_section(self, s: Optional[str]) -> None:
        Echo("")
        Secho(s, fg=self.section_color, bold=True)

    def print_value(self, name: str, value: Any) -> None:
        Echo(click.style(name + ": ") + click.style(value, fg=self.value_color))

    def print_warning(self, s: str) -> None:
        Secho(f"WARNING: {s}", fg=self.warning_color)