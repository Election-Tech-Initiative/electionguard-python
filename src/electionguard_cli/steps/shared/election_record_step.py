from shutil import make_archive
from os.path import splitext, dirname, basename
from tempfile import TemporaryDirectory
from click import echo
from electionguard import to_file
from electionguard.constants import get_constants

from electionguard_cli.cli_models import BuildElectionResults, E2eSubmitResults
from electionguard_cli.cli_models.e2e_decrypt_results import E2eDecryptResults
from electionguard_cli.cli_models.e2e.e2e_inputs import E2eInputs

from electionguard_tools.helpers.export import export_record

from .cli_step_base import CliStepBase


class ElectionRecordStep(CliStepBase):
    """Responsible for publishing an election record after an election has completed."""

    _COMPRESSION_FORMAT = "zip"

    def export(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: E2eDecryptResults,
    ) -> None:

        self.print_header("Election Record")

        self._export_election_record(
            election_inputs, build_election_results, submit_results, decrypt_results
        )
        self._export_private_keys(election_inputs)

    def _export_election_record(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: E2eDecryptResults,
    ) -> None:
        guardian_records = [
            guardian.publish() for guardian in election_inputs.guardians
        ]
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

    def _export_private_keys(self, election_inputs: E2eInputs) -> None:
        if election_inputs.output_keys is None:
            return

        private_guardian_records = [
            guardian.export_private_data() for guardian in election_inputs.guardians
        ]
        file_path = election_inputs.output_keys
        for private_guardian_record in private_guardian_records:
            file_name = private_guardian_record.guardian_id
            to_file(private_guardian_record, file_name, file_path)
        echo(
            f"Exported {len(private_guardian_records)} private guardian keys to '{election_inputs.output_keys}'"
        )
        self.print_warning(
            f"The files in {file_path} can decrypt an entire election. Protect the folder securely and do not share it."
        )
