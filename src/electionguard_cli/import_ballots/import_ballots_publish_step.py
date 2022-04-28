from ..cli_steps import OutputStepBase


class ImportBallotsPublishStep(OutputStepBase):
    """Responsible for publishing an election record during an import ballots command"""

    def publish(self) -> None:
        self.print_header("Publishing Results")
