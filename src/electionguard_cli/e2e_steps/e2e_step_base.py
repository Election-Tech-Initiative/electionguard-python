from typing import Any
import click


class E2eStepBase:
    """
    Responsible for providing common functionality to the individual steps within an end-to-end election command
    from the CLI.
    """

    def print_header(self, s: str) -> None:
        click.secho(f"{'-'*40}", fg="green")
        click.secho(s, fg="green")
        click.secho(f"{'-'*40}", fg="green")

    def print_value(self, name: str, value: Any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg="yellow"))
