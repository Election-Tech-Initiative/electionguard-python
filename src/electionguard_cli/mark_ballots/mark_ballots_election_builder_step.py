from ..cli_models import BuildElectionResults
from ..cli_steps import ElectionBuilderStep
from .mark_ballot_inputs import MarkBallotInputs


class MarkBallotsElectionBuilderStep(ElectionBuilderStep):
    """Responsible for creating a manifest and context for use in an election
    specifically for the mark ballots command"""

    def build_election_with_context(
        self, election_inputs: MarkBallotInputs
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
