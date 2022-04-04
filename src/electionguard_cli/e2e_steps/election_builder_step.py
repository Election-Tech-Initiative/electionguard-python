from typing import Tuple

from e2e_steps.e2e_step_base import E2eStepBase
from electionguard.key_ceremony import ElectionJointKey
from electionguard.election import CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.manifest import InternalManifest, Manifest
from electionguard.utils import get_optional


class ElectionBuilderStep(E2eStepBase):
    """Responsible for creating a manifest and context for use in an election."""

    def build_election(
        self,
        joint_key: ElectionJointKey,
        guardian_count: int,
        quorum: int,
        manifest: Manifest,
    ) -> Tuple[InternalManifest, CiphertextElectionContext]:
        self.print_header("Building election")

        election_builder = ElectionBuilder(guardian_count, quorum, manifest)
        election_builder.set_public_key(joint_key.joint_public_key)
        election_builder.set_commitment_hash(joint_key.commitment_hash)
        build_result = election_builder.build()
        return get_optional(build_result)
