from os.path import join
from electionguard.serialize import to_file
from electionguard.constants import get_constants
from electionguard_tools.helpers.export import CONSTANTS_FILE_NAME

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
        self._export_constants(setup_inputs)
        # todo: GuardianRecord.json

        self._export_guardian_private_keys(setup_inputs)

    def _export_constants(self, setup_inputs: SetupInputs) -> None:
        constants = get_constants()
        to_file(constants, CONSTANTS_FILE_NAME, setup_inputs.out)
        location = join(setup_inputs.out, CONSTANTS_FILE_NAME + ".json")
        self.print_value("Election constants", location)

    def _export_guardian_private_keys(self, setup_inputs: SetupInputs) -> None:
        guardian_keys_dir = join(setup_inputs.out, "guardian_private_data")
        self._export_private_keys(guardian_keys_dir, setup_inputs.guardians)
