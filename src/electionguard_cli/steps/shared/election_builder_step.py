from electionguard.elgamal import ElGamalPublicKey
from electionguard.group import ElementModQ
from electionguard.key_ceremony import ElectionJointKey
from electionguard.election_builder import ElectionBuilder
from electionguard.utils import get_optional
from electionguard_cli.cli_models.e2e.e2e_inputs import CliElectionInputsBase

from electionguard_cli.cli_models import BuildElectionResults
from electionguard_cli.cli_models.import_ballots.import_ballot_inputs import (
    ImportBallotInputs,
)
from .cli_step_base import CliStepBase


class ElectionBuilderStep(CliStepBase):
    """Responsible for creating a manifest and context for use in an election."""

    def build_election_with_key(
        self,
        election_inputs: CliElectionInputsBase,
        joint_key: ElectionJointKey,
    ) -> BuildElectionResults:
        return self._build_election(
            election_inputs, joint_key.joint_public_key, joint_key.commitment_hash
        )

    def build_election_with_context(
        self, election_inputs: ImportBallotInputs
    ) -> BuildElectionResults:
        return self._build_election(
            election_inputs,
            election_inputs.context.elgamal_public_key,
            election_inputs.context.commitment_hash,
        )

    def _build_election(
        self,
        election_inputs: CliElectionInputsBase,
        joint_public_key: ElGamalPublicKey,
        committment_hash: ElementModQ,
    ) -> BuildElectionResults:
        self.print_header("Building election")

        election_builder = ElectionBuilder(
            election_inputs.guardian_count,
            election_inputs.quorum,
            election_inputs.manifest,
        )
        election_builder.set_public_key(joint_public_key)
        election_builder.set_commitment_hash(committment_hash)
        build_result = election_builder.build()
        internal_manifest, context = get_optional(build_result)
        return BuildElectionResults(internal_manifest, context)
