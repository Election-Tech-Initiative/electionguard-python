from typing import Any, Optional
import click


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
        click.echo("")
        click.secho(f"{'-'*40}", fg=self.header_color)
        click.secho(s, fg=self.header_color)
        click.secho(f"{'-'*40}", fg=self.header_color)

    def print_section(self, s: Optional[str]) -> None:
        click.echo("")
        click.secho(s, fg=self.section_color, bold=True)

    def print_value(self, name: str, value: Any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg=self.value_color))

    def print_warning(self, s: str) -> None:
        click.secho(f"WARNING: {s}", fg=self.warning_color)
