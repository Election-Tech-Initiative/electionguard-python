from shutil import rmtree, make_archive
from os import remove
import click
from electionguard_cli.cli_models import BuildElectionResults, E2eSubmitResults
from electionguard_cli.cli_models.e2e_decrypt_results import E2eDecryptResults
from electionguard_cli.cli_models.e2e_inputs import E2eInputs
from electionguard_cli.e2e_steps.e2e_step_base import E2eStepBase
from electionguard.constants import get_constants

from electionguard_tools.helpers.export import (
    PRIVATE_DATA_DIR,
    ELECTION_RECORD_DIR,
    export_private_data,
    export_record,
)


class ElectionRecordStep(E2eStepBase):
    """Responsible for publishing an election record after an election has completed."""

    REMOVE_RAW_OUTPUT = True
    REMOVE_ZIP_OUTPUT = True

    def run(
        self,
        election_inputs: E2eInputs,
        build_election_results: BuildElectionResults,
        submit_results: E2eSubmitResults,
        decrypt_results: E2eDecryptResults,
    ) -> None:
        self.print_header("Election Record")
        click.echo(f"Exporting to {election_inputs.output_path}")
        guardian_records = [
            guardian.publish() for guardian in election_inputs.guardians
        ]
        private_guardian_records = [
            guardian.export_private_data() for guardian in election_inputs.guardians
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
        )

        export_private_data(
            election_inputs.ballots,
            submit_results.ciphertext_ballots,
            private_guardian_records,
        )
        click.echo(f"Private data exported to: {PRIVATE_DATA_DIR}")

        ZIP_SUFFIX = "zip"
        make_archive(ELECTION_RECORD_DIR, ZIP_SUFFIX, ELECTION_RECORD_DIR)
        make_archive(PRIVATE_DATA_DIR, ZIP_SUFFIX, PRIVATE_DATA_DIR)

        if self.REMOVE_RAW_OUTPUT:
            rmtree(ELECTION_RECORD_DIR)
            rmtree(PRIVATE_DATA_DIR)

        if self.REMOVE_ZIP_OUTPUT:
            remove(f"{ELECTION_RECORD_DIR}.{ZIP_SUFFIX}")
            remove(f"{PRIVATE_DATA_DIR}.{ZIP_SUFFIX}")
