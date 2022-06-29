from electionguard.key_ceremony import ElectionJointKey
from .e2e_inputs import E2eInputs
from ..cli_models import BuildElectionResults
from ..cli_steps import ElectionBuilderStep


class E2eElectionBuilderStep(ElectionBuilderStep):
    """Responsible for creating a manifest and context for use in an election"""

    def build_election_with_key(
        self, election_inputs: E2eInputs, joint_key: ElectionJointKey
    ) -> BuildElectionResults:
        return self._build_election(
            election_inputs,
            joint_key.joint_public_key,
            joint_key.commitment_hash,
            election_inputs.verification_url,
        )
