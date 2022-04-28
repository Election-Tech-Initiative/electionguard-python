from .import_ballot_inputs import ImportBallotInputs
from ..cli_models import CliDecryptResults, BuildElectionResults
from ..cli_steps import OutputStepBase


class ImportBallotsPublishStep(OutputStepBase):
    """Responsible for publishing an election record during an import ballots command"""

    def publish(
        self,
        election_inputs: ImportBallotInputs,
        build_election_results: BuildElectionResults,
        decrypt_results: CliDecryptResults,
    ) -> None:
        self.print_header("Publishing Results")
