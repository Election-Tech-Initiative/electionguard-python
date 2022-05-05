from click import echo

from electionguard import to_file

from ..cli_models import EncryptResults
from ..cli_steps import OutputStepBase


class EncryptBallotsPublishStep(OutputStepBase):
    """Responsible for writing the results of the encrypt ballots command."""

    def publish(self, encrypt_results: EncryptResults, out_dir: str) -> None:
        if out_dir is None:
            return
        self.print_header("Writing Encrypted Ballots")
        device_file = to_file(encrypt_results.device, "device", out_dir)
        self.print_value("Device file", device_file + ".json")
        for ballot in encrypt_results.ciphertext_ballots:
            ballot_file = to_file(ballot, ballot.object_id, out_dir)
            echo(f"Writing {ballot_file}")
        self.print_value("Encrypted ballots", len(encrypt_results.ciphertext_ballots))
