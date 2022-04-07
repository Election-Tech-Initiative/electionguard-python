import click
from electionguard_cli.e2e_steps.e2e_step_base import E2eStepBase


class ElectionRecordStep(E2eStepBase):
    """Responsible for publishing an election record after an election has completed."""

    def run(self, output_path: str):
        self.print_header("Election Record")
        click.echo(output_path)
