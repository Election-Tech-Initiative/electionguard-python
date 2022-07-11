from typing import List, Any

from electionguard import to_file
from electionguard.guardian import Guardian, GuardianRecord
from electionguard_tools.helpers.export import GUARDIAN_PREFIX

from .cli_step_base import CliStepBase
from ..cli_models import CliElectionInputsBase


class OutputStepBase(CliStepBase):
    """Responsible for common functionality across all CLI commands related to outputting results."""

    _COMPRESSION_FORMAT = "zip"

    def _export_private_keys(self, output_keys: str, guardians: List[Guardian]) -> None:
        if output_keys is None:
            return

        private_guardian_records = [
            guardian.export_private_data() for guardian in guardians
        ]
        file_path = output_keys
        for private_guardian_record in private_guardian_records:
            file_name = GUARDIAN_PREFIX + private_guardian_record.guardian_id
            to_file(private_guardian_record, file_name, file_path)
        self.print_value("Guardian private keys", output_keys)
        self.print_warning(
            f"The files in {file_path} are secret and should be protected securely and not shared."
        )

    @staticmethod
    def _get_guardian_records(
        election_inputs: CliElectionInputsBase,
    ) -> List[GuardianRecord]:
        return [guardian.publish() for guardian in election_inputs.guardians]

    def _export_file(
        self,
        title: str,
        content: Any,
        file_dir: str,
        file_name: str,
    ) -> str:
        location = to_file(content, file_name, file_dir)
        self.print_value(title, location)
        return location
