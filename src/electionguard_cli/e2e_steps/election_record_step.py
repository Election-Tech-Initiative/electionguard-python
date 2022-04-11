from shutil import rmtree, make_archive
import click
from electionguard_cli.cli_models import BuildElectionResults, E2eSubmitResults
from electionguard_cli.cli_models.e2e_decrypt_results import E2eDecryptResults
from electionguard_cli.cli_models.e2e_inputs import E2eInputs
from electionguard_cli.e2e_steps.e2e_step_base import E2eStepBase
from electionguard.constants import get_constants

from electionguard_tools.helpers.export import (
    ELECTION_RECORD_DIR,
    export_record,
)


class ElectionRecordStep(E2eStepBase):
    """Responsible for publishing an election record after an election has completed."""

    REMOVE_RAW_OUTPUT = True
    REMOVE_ZIP_OUTPUT = True
    COMPRESSION_FORMAT = "zip"

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
            election_record_directory=ELECTION_RECORD_DIR,
        )
        make_archive(ELECTION_RECORD_DIR, self.COMPRESSION_FORMAT, ELECTION_RECORD_DIR)
        if self.REMOVE_RAW_OUTPUT:
            rmtree(ELECTION_RECORD_DIR)
