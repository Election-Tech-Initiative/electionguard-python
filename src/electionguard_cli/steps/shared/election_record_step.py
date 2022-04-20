from shutil import make_archive
from os.path import splitext
from tempfile import TemporaryDirectory
from click import echo
from electionguard_cli.cli_models import BuildElectionResults, E2eSubmitResults
from electionguard_cli.cli_models.e2e_decrypt_results import E2eDecryptResults
from electionguard_cli.cli_models.e2e_inputs import E2eInputs
from electionguard.constants import get_constants

from electionguard_tools.helpers.export import export_record

from .cli_step_base import CliStepBase


class ElectionRecordStep(CliStepBase):
    """Responsible for publishing an election record after an election has completed."""

    _COMPRESSION_FORMAT = "zip"

    def run(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: E2eDecryptResults,
    ) -> None:

        self.print_header("Election Record")
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
            echo(
                f"Successfully exported election record to '{election_inputs.output_record}'"
            )
