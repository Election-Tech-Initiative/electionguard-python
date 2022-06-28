from ..cli_models import BuildElectionResults
from ..cli_steps import ElectionBuilderStep
from .import_ballot_inputs import ImportBallotInputs


class ImportBallotsElectionBuilderStep(ElectionBuilderStep):
    """Responsible for creating a manifest and context for use in an election
    specifically for the import ballots command"""

    def build_election_with_context(
        self, election_inputs: ImportBallotInputs
    ) -> BuildElectionResults:
        verification_url = election_inputs.context.get_extended_data_field(
            self.verification_url_name
        )
        return self._build_election(
            election_inputs,
            election_inputs.context.elgamal_public_key,
            election_inputs.context.commitment_hash,
            verification_url,
        )
