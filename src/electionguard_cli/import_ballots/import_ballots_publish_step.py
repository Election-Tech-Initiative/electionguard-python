from typing import List
from shutil import make_archive
from os.path import splitext
from tempfile import TemporaryDirectory
from click import echo
from electionguard.encrypt import EncryptionDevice

from electionguard.constants import get_constants
from electionguard_tools.helpers.export import export_record

from .import_ballot_inputs import ImportBallotInputs
from ..cli_models import CliDecryptResults, BuildElectionResults
from ..cli_steps import OutputStepBase


class ImportBallotsPublishStep(OutputStepBase):
    """Responsible for publishing an election record during an import ballots command"""

    def publish(
        self,
        election_inputs: ImportBallotInputs,
        build_election_results: BuildElectionResults,
        decrypt_results: CliDecryptResults,
    ) -> None:

        if election_inputs.output_record is None:
            return

        self.print_header("Publishing Results")

        guardian_records = OutputStepBase._get_guardian_records(election_inputs)
        constants = get_constants()

        encryption_devices: List[EncryptionDevice] = election_inputs.encryption_devices

        with TemporaryDirectory() as temp_dir:
            export_record(
                election_inputs.manifest,
                build_election_results.context,
                constants,
                encryption_devices,
                election_inputs.submitted_ballots,
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
