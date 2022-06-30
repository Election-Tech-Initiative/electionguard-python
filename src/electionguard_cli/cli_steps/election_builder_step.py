from typing import Optional
import click
from electionguard.elgamal import ElGamalPublicKey
from electionguard.group import ElementModQ
from electionguard.utils import get_optional
from electionguard_tools.helpers.election_builder import ElectionBuilder

from ..cli_models import CliElectionInputsBase, BuildElectionResults
from .cli_step_base import CliStepBase


class ElectionBuilderStep(CliStepBase):
    """Responsible for creating a manifest and context for use in an election."""

    def _build_election(
        self,
        election_inputs: CliElectionInputsBase,
        joint_public_key: ElGamalPublicKey,
        committment_hash: ElementModQ,
        verification_url: Optional[str],
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
        if verification_url is not None:
            election_builder.add_extended_data_field(
                self.VERIFICATION_URL_NAME, verification_url
            )
        click.echo("Creating context and internal manifest")
        build_result = election_builder.build()
        internal_manifest, context = get_optional(build_result)
        return BuildElectionResults(internal_manifest, context)
