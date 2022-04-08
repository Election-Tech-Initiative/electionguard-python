from electionguard.key_ceremony import ElectionKey
from electionguard.election_builder import ElectionBuilder
from electionguard.utils import get_optional

from ..cli_models import E2eInputs, BuildElectionResults
from .e2e_step_base import E2eStepBase


class ElectionBuilderStep(E2eStepBase):
    """Responsible for creating a manifest and context for use in an election."""

    def build_election(
        self,
        election_inputs: E2eInputs,
        election_key: ElectionKey,
    ) -> BuildElectionResults:
        self.print_header("Building election")

        election_builder = ElectionBuilder(
            election_inputs.guardian_count,
            election_inputs.quorum,
            election_inputs.manifest,
        )
        election_builder.set_public_key(election_key.public_key)
        election_builder.set_commitment_hash(election_key.commitment_hash)
        build_result = election_builder.build()
        internal_manifest, context = get_optional(build_result)
        return BuildElectionResults(internal_manifest, context)
