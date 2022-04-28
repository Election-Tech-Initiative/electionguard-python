from shutil import make_archive
from os.path import splitext
from tempfile import TemporaryDirectory
from click import echo
from electionguard.constants import get_constants

from electionguard_tools.helpers.export import export_record

from .e2e_inputs import E2eInputs
from ..cli_models import BuildElectionResults, E2eSubmitResults, CliDecryptResults
from ..cli_steps import OutputStepBase


class E2eElectionRecordStep(OutputStepBase):
    """Responsible for publishing an election record after an election has completed."""

    _COMPRESSION_FORMAT = "zip"

    def export(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: CliDecryptResults,
    ) -> None:

        self.print_header("Election Record")

        self._export_election_record(
            election_inputs, build_election_results, submit_results, decrypt_results
        )
        self._export_private_keys_e2e(election_inputs)

    def _export_election_record(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: CliDecryptResults,
    ) -> None:
        guardian_records = OutputStepBase._get_guardian_records(election_inputs)
        constants = get_constants()
        with TemporaryDirectory() as temp_dir:
            export_record(
                election_inputs.manifest,
                build_election_results.context,
                constants,
                [submit_results.device],
                submit_results.data_store.all(),
                decrypt_results.plaintext_spoiled_ballots.values(),
                decrypt_results.ciphertext_tally.publish(),
                decrypt_results.plaintext_tally,
                guardian_records,
                decrypt_results.lagrange_coefficients,
                election_record_directory=temp_dir,
            )
            file_name = splitext(election_inputs.output_record)[0]
            make_archive(file_name, self._COMPRESSION_FORMAT, temp_dir)
            echo(f"Exported election record to '{election_inputs.output_record}'")

    def _export_private_keys_e2e(self, election_inputs: E2eInputs) -> None:
        self._export_private_keys(
            election_inputs.output_keys, election_inputs.guardians
        )
