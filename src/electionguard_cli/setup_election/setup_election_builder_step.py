from electionguard import ElectionJointKey

from .setup_inputs import SetupInputs
from ..cli_models import BuildElectionResults
from ..cli_steps import ElectionBuilderStep


class SetupElectionBuilderStep(ElectionBuilderStep):
    """Responsible for creating a manifest and context for use in an election
    specifically for the import ballots command"""

    def build_election_for_setup(
        self, election_inputs: SetupInputs, joint_key: ElectionJointKey
    ) -> BuildElectionResults:
        return self._build_election(
            election_inputs,
            joint_key.joint_public_key,
            joint_key.commitment_hash,
            election_inputs.verification_url,
        )
