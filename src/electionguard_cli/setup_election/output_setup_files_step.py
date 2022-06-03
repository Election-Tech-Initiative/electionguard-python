from os import path
from os.path import join
from shutil import make_archive, rmtree
from electionguard.election import CiphertextElectionContext
from electionguard.serialize import to_file
from electionguard.constants import get_constants
from electionguard_tools.helpers.export import (
    CONSTANTS_FILE_NAME,
    CONTEXT_FILE_NAME,
    GUARDIAN_PREFIX,
    MANIFEST_FILE_NAME,
)

from .setup_inputs import SetupInputs
from ..cli_models.e2e_build_election_results import BuildElectionResults
from ..cli_steps import OutputStepBase

ENCRYPTION_PACKAGE_DIR = "public_encryption_package"


class OutputSetupFilesStep(OutputStepBase):
    """Responsible for outputting the files necessary to setup an election"""

    def output(
        self, setup_inputs: SetupInputs, build_election_results: BuildElectionResults
    ) -> None:
        self.print_header("Generating Output")
        self._export_context(setup_inputs, build_election_results.context)
        self._export_constants(setup_inputs)
        self._export_manifest(setup_inputs)
        self._export_guardian_records(setup_inputs)
        if setup_inputs.zip:
            self._zip(setup_inputs)
        self._export_guardian_private_keys(setup_inputs)

    def _zip(self, setup_inputs: SetupInputs) -> None:
        dir_to_zip = path.join(setup_inputs.out, ENCRYPTION_PACKAGE_DIR)
        file_name = path.join(setup_inputs.out, ENCRYPTION_PACKAGE_DIR)
        make_archive(file_name, self._COMPRESSION_FORMAT, dir_to_zip)
        rmtree(dir_to_zip)
        self.print_value("Election record", f"{file_name}.{self._COMPRESSION_FORMAT}")

    def _export_context(
        self, setup_inputs: SetupInputs, context: CiphertextElectionContext
    ) -> None:
        out_dir = path.join(setup_inputs.out, ENCRYPTION_PACKAGE_DIR)
        self._export_file("Context", context, out_dir, CONTEXT_FILE_NAME)

    def _export_constants(self, setup_inputs: SetupInputs) -> None:
        constants = get_constants()
        out_dir = path.join(setup_inputs.out, ENCRYPTION_PACKAGE_DIR)
        self._export_file("Constants", constants, out_dir, CONSTANTS_FILE_NAME)

    def _export_manifest(self, setup_inputs: SetupInputs) -> None:
        out_dir = path.join(setup_inputs.out, ENCRYPTION_PACKAGE_DIR)
        self._export_file(
            "Manifest",
            setup_inputs.manifest,
            out_dir,
            MANIFEST_FILE_NAME,
        )

    def _export_guardian_records(self, setup_inputs: SetupInputs) -> None:
        guardian_records_dir = join(
            setup_inputs.out, ENCRYPTION_PACKAGE_DIR, "guardians"
        )
        guardian_records = OutputStepBase._get_guardian_records(setup_inputs)
        for guardian_record in guardian_records:
            to_file(
                guardian_record,
                GUARDIAN_PREFIX + guardian_record.guardian_id,
                guardian_records_dir,
            )
        self.print_value("Guardian records", guardian_records_dir)

    def _export_guardian_private_keys(self, setup_inputs: SetupInputs) -> None:
        guardian_keys_dir = join(setup_inputs.out, "private_guardian_data")
        self._export_private_keys(guardian_keys_dir, setup_inputs.guardians)
