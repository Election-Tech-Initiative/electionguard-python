from io import TextIOWrapper
from os import listdir
from os.path import join
from typing import List
from click import echo
from electionguard import CiphertextElectionContext

from electionguard.ballot import SubmittedBallot
from electionguard.manifest import Manifest
from electionguard.serialize import (
    from_file,
)
from electionguard_cli.cli_models.import_ballots.import_ballot_inputs import (
    ImportBallotInputs,
)
from electionguard_cli.steps.shared.input_retrieval_step_base import (
    InputRetrievalStepBase,
)


class ImportBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's import ballots command."""

    def get_inputs(
        self,
        guardian_count: int,
        quorum: int,
        manifest_file: TextIOWrapper,
        ballots_dir: str,
    ) -> ImportBallotInputs:
        self.print_header("Retrieving Inputs")
        guardians = InputRetrievalStepBase._get_guardians(guardian_count, quorum)
        manifest: Manifest = self._get_manifest(manifest_file)
        self.print_value("Guardians", guardian_count)
        self.print_value("Quorum", quorum)
        submitted_ballots = ImportBallotsInputRetrievalStep._get_ballots(ballots_dir)
        context = self._get_context()

        # todo: instead of printing import ballots from ballots dir
        self.print_value("Ballots Dir", ballots_dir)

        return ImportBallotInputs(
            guardian_count, quorum, guardians, manifest, submitted_ballots, context
        )

    @staticmethod
    def _get_context() -> CiphertextElectionContext:
        # todo: parameterize
        return from_file(CiphertextElectionContext, "data/simple/context.json")

    @staticmethod
    def _get_ballots(ballots_dir: str) -> List[SubmittedBallot]:
        files = listdir(ballots_dir)

        submitted_ballots: List[SubmittedBallot] = []
        for filename in files:
            full_file = join(ballots_dir, filename)
            echo(f"importing {full_file}")
            submitted_ballot = from_file(SubmittedBallot, full_file)
            submitted_ballots.append(submitted_ballot)
        return submitted_ballots
