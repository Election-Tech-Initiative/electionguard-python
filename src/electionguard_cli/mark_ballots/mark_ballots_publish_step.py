from click import echo

from electionguard import to_file

from ..cli_models import MarkResults
from ..cli_steps import OutputStepBase


class MarkBallotsPublishStep(OutputStepBase):
    """Responsible for writing the results of the mark ballots command."""

    def publish(self, marked_ballots: MarkResults, out_dir: str) -> None:
        if out_dir is None:
            return
        self.print_header("Writing Marked Ballots")
        for ballot in marked_ballots.plaintext_ballots:
            ballot_file = to_file(ballot, ballot.object_id, out_dir)
            echo(f"Writing {ballot_file}")
        self.print_value("Marked ballots", len(marked_ballots.plaintext_ballots))
