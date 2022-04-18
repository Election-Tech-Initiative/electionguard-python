from io import TextIOWrapper
from typing import List

from electionguard.ballot import PlaintextBallot
from electionguard.manifest import Manifest
from electionguard.serialize import (
    from_list_in_file_wrapper,
)
from electionguard_cli.cli_models.e2e_inputs import E2eInputs
from electionguard_cli.e2e_steps.shared.input_retrieval_step_base import (
    InputRetrievalStepBase,
)


class E2eInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's e2e command."""

    def get_inputs(
        self,
        guardian_count: int,
        quorum: int,
        manifest_file: TextIOWrapper,
        ballots_file: TextIOWrapper,
        spoil_id: str,
        output_file: str,
    ) -> E2eInputs:
        self.print_header("Retrieving Inputs")
        guardians = InputRetrievalStepBase._get_guardians(guardian_count, quorum)
        manifest: Manifest = self._get_manifest(manifest_file)
        ballots = E2eInputRetrievalStep._get_ballots(ballots_file)
        self.print_value("Guardians", guardian_count)
        self.print_value("Quorum", quorum)
        return E2eInputs(
            guardian_count, quorum, guardians, manifest, ballots, spoil_id, output_file
        )

    @staticmethod
    def _get_ballots(ballots_file: TextIOWrapper) -> List[PlaintextBallot]:
        ballots: List[PlaintextBallot] = from_list_in_file_wrapper(
            PlaintextBallot, ballots_file
        )
        return ballots
