from os import path
from os.path import join
from typing import Optional

import click
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


class OutputSetupFilesStep(OutputStepBase):
    """Responsible for outputting the files necessary to setup an election"""

    def output(
        self,
        setup_inputs: SetupInputs,
        build_election_results: BuildElectionResults,
        package_dir: str,
        keys_dir: Optional[str],
    ) -> None:
        self.print_header("Generating Output")
        self._export_context(build_election_results.context, package_dir)
        self._export_constants(package_dir)
        self._export_manifest(setup_inputs, package_dir)
        self._export_guardian_records(setup_inputs, package_dir)
        if keys_dir is not None:
            self._export_guardian_private_keys(setup_inputs, keys_dir)

    def _export_context(
        self,
        context: CiphertextElectionContext,
        out_dir: str,
    ) -> str:
        return self._export_file("Context", context, out_dir, CONTEXT_FILE_NAME)

    def _export_constants(self, out_dir: str) -> str:
        constants = get_constants()
        return self._export_file("Constants", constants, out_dir, CONSTANTS_FILE_NAME)

    def _export_manifest(self, setup_inputs: SetupInputs, out_dir: str) -> None:
        self._export_file(
            "Manifest",
            setup_inputs.manifest,
            out_dir,
            MANIFEST_FILE_NAME,
        )

    def _export_guardian_records(self, setup_inputs: SetupInputs, out_dir: str) -> None:
        guardian_records_dir = join(out_dir, "guardians")
        guardian_records = OutputStepBase._get_guardian_records(setup_inputs)
        for guardian_record in guardian_records:
            to_file(
                guardian_record,
                GUARDIAN_PREFIX + guardian_record.guardian_id,
                guardian_records_dir,
            )
        self.print_value("Guardian records", guardian_records_dir)

    def _export_guardian_private_keys(self, inputs: SetupInputs, keys_dir: str) -> None:
        if path.exists(keys_dir) and not inputs.force:
            confirm = click.confirm(
                "Existing guardian keys found, are you sure you want to overwrite them?",
                default=True,
            )
            if not confirm:
                return
        self._export_private_keys(keys_dir, inputs.guardians)
