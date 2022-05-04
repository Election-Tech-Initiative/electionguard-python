from typing import List
from io import TextIOWrapper
from os import listdir
from os.path import join
from click import echo

from electionguard.ballot import PlaintextBallot
from electionguard.manifest import Manifest
from electionguard.serialize import from_file

from .encrypt_ballot_inputs import EncryptBallotInputs
from ..cli_steps import (
    InputRetrievalStepBase,
)


class EncryptBallotsInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's encrypt ballots command."""

    def get_inputs(
        self,
        manifest_file: TextIOWrapper,
        context_file: TextIOWrapper,
        ballots_dir: str,
    ) -> EncryptBallotInputs:

        self.print_header("Retrieving Inputs")
        manifest: Manifest = self._get_manifest(manifest_file)
        context = InputRetrievalStepBase._get_context(context_file)
        plaintext_ballots = EncryptBallotsInputRetrievalStep._get_ballots(ballots_dir)

        return EncryptBallotInputs(
            manifest,
            context,
            plaintext_ballots,
        )

    @staticmethod
    def _get_ballots(ballots_dir: str) -> List[PlaintextBallot]:
        files = listdir(ballots_dir)

        return [
            EncryptBallotsInputRetrievalStep._get_ballot(ballots_dir, f) for f in files
        ]

    @staticmethod
    def _get_ballot(ballots_dir: str, filename: str) -> PlaintextBallot:
        full_file = join(ballots_dir, filename)
        echo(f"importing {filename}")
        return from_file(PlaintextBallot, full_file)
