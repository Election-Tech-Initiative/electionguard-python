from typing import Any, Optional
from electionguard_cli.print_utils import print_header, print_warning_utils
#import click
from print_utils import print_header_utils, print_message_utils, print_value_utils

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
        print_header_utils(s)
        #click.echo("")
        #click.secho(f"{'-'*40}", fg=self.header_color)
        #click.secho(s, fg=self.header_color)
        #click.secho(f"{'-'*40}", fg=self.header_color)

    def print_section(self, s: Optional[str]) -> None:
        print_message_utils(s)
        #click.echo("")
        #click.secho(s, fg=self.section_color, bold=True)

    def print_value(self, name: str, value: Any) -> None:
        print_value_utils(name, value)
        #click.echo(click.style(name + ": ") + click.style(value, fg=self.value_color))

    def print_warning(self, s: str) -> None:
        print_warning_utils(s)
        #click.secho(f"WARNING: {s}", fg=self.warning_color)

