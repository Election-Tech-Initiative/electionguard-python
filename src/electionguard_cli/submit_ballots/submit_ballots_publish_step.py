from click import echo

from electionguard import to_file

from ..cli_models import SubmitResults
from ..cli_steps import OutputStepBase


class SubmitBallotsPublishStep(OutputStepBase):
    """Responsible for writing the results of the submit ballots command."""

    def publish(self, submit_results: SubmitResults, out_dir: str) -> None:
        if out_dir is None:
            return
        self.print_header("Writing Submitted Ballots")
        for ballot in submit_results.submitted_ballots:
            ballot_file = to_file(ballot, ballot.object_id, out_dir)
            echo(f"Writing {ballot_file}")
        self.print_value("Submitted ballots", len(submit_results.submitted_ballots))
