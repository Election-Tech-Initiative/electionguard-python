from ..cli_models import BuildElectionResults
from ..cli_steps import ElectionBuilderStep
from .submit_ballot_inputs import SubmitBallotInputs


class SubmitBallotsElectionBuilderStep(ElectionBuilderStep):
    """Responsible for creating a manifest and context for use in an election
    specifically for the submit ballots command"""

    def build_election_with_context(
        self, election_inputs: SubmitBallotInputs
    ) -> BuildElectionResults:
        verification_url = election_inputs.context.get_extended_data_field(
            self.VERIFICATION_URL_NAME
        )
        return self._build_election(
            election_inputs,
            election_inputs.context.elgamal_public_key,
            election_inputs.context.commitment_hash,
            verification_url,
        )
