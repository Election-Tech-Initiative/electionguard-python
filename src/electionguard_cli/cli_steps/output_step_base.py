from typing import List
from click import echo

from electionguard import to_file
from electionguard.guardian import Guardian

from .cli_step_base import CliStepBase


class OutputStepBase(CliStepBase):
    """Responsible for common functionality across all CLI commands related to outputting results."""

    def _export_private_keys(self, output_keys: str, guardians: List[Guardian]) -> None:
        if output_keys is None:
            return

        private_guardian_records = [
            guardian.export_private_data() for guardian in guardians
        ]
        file_path = output_keys
        for private_guardian_record in private_guardian_records:
            file_name = private_guardian_record.guardian_id
            to_file(private_guardian_record, file_name, file_path)
        self.print_value("Guardian private keys", output_keys)
        self.print_warning(
            f"The files in {file_path} are secret and should be protected securely and not shared publicly."
        )
