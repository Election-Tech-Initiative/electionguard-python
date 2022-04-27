import os
from .setup_inputs import SetupInputs
from ..cli_models.e2e_build_election_results import BuildElectionResults
from ..cli_steps import OutputStepBase


class OutputSetupFilesStep(OutputStepBase):
    """Responsible for outputting the files necessary to setup an election"""

    def output(
        self, setup_inputs: SetupInputs, build_election_results: BuildElectionResults
    ) -> None:
        self.print_header("Generating Output")

        # todo: output CiphertextElectionContext.json
        # todo: output ElectionConstants.json
        # todo: GuardianRecord.json

        # GuardianKeyPair.json
        guardian_keys_dir = os.path.join(setup_inputs.out, "guardian_private_data")
        self._export_private_keys(guardian_keys_dir, setup_inputs.guardians)
