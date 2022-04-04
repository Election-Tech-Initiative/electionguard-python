import click

class E2eStepBase:
    def print_header(self, s: str) -> None:
        click.secho(f"{'-'*40}", fg='green')
        click.secho(s, fg='green')
        click.secho(f"{'-'*40}", fg='green')

    def print_value(self, name: str, value: any) -> None:
        click.echo(click.style(name + ": ") + click.style(value, fg='yellow'))

