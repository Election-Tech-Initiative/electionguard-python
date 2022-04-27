from ..cli_models.e2e_build_election_results import BuildElectionResults
from ..cli_steps import CliStepBase


class OutputSetupFilesStep(CliStepBase):
    """Responsible for outputting the files necessary to setup an election"""

    def output(self, build_election_results: BuildElectionResults) -> None:
        self.print_header("Generating Output")
