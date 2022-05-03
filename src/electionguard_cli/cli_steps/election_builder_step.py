import click
from electionguard.elgamal import ElGamalPublicKey
from electionguard.group import ElementModQ
from electionguard.key_ceremony import ElectionJointKey
from electionguard.election_builder import ElectionBuilder
from electionguard.utils import get_optional

from ..cli_models import CliElectionInputsBase, BuildElectionResults
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

    def _build_election(
        self,
        election_inputs: CliElectionInputsBase,
        joint_public_key: ElGamalPublicKey,
        committment_hash: ElementModQ,
    ) -> BuildElectionResults:
        self.print_header("Building election")

        click.echo("Initializing public key and commitment hash")
        election_builder = ElectionBuilder(
            election_inputs.guardian_count,
            election_inputs.quorum,
            election_inputs.manifest,
        )
        election_builder.set_public_key(joint_public_key)
        election_builder.set_commitment_hash(committment_hash)
        click.echo("Creating context and internal manifest")
        build_result = election_builder.build()
        internal_manifest, context = get_optional(build_result)
        return BuildElectionResults(internal_manifest, context)
