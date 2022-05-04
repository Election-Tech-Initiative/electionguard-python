from io import TextIOWrapper
from typing import List
from os.path import isfile, isdir, join
from os import listdir
from click import echo

from electionguard.ballot import PlaintextBallot
from electionguard.key_ceremony import CeremonyDetails
from electionguard.manifest import Manifest
from electionguard.serialize import from_list_in_file, from_file
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)

from ..cli_steps import (
    InputRetrievalStepBase,
)
from .e2e_inputs import E2eInputs


class E2eInputRetrievalStep(InputRetrievalStepBase):
    """Responsible for retrieving and parsing user provided inputs for the CLI's e2e command."""

    def get_inputs(
        self,
        guardian_count: int,
        quorum: int,
        manifest_file: TextIOWrapper,
        ballots_path: str,
        spoil_id: str,
        output_record: str,
        output_keys: str,
    ) -> E2eInputs:
        self.print_header("Retrieving Inputs")
        guardians = KeyCeremonyOrchestrator.create_guardians(
            CeremonyDetails(guardian_count, quorum)
        )
        manifest: Manifest = self._get_manifest(manifest_file)
        ballots = E2eInputRetrievalStep._get_ballots(ballots_path)
        self.print_value("Guardians", guardian_count)
        self.print_value("Quorum", quorum)
        return E2eInputs(
            guardian_count,
            quorum,
            guardians,
            manifest,
            ballots,
            spoil_id,
            output_record,
            output_keys,
        )

    @staticmethod
    def _get_ballots(ballots_path: str) -> List[PlaintextBallot]:
        if isfile(ballots_path):
            return from_list_in_file(PlaintextBallot, ballots_path)
        if isdir(ballots_path):
            files = listdir(ballots_path)
            return [E2eInputRetrievalStep._get_ballot(ballots_path, f) for f in files]
        raise ValueError(
            f"{ballots_path} is neither a valid file nor a valid directory"
        )

    @staticmethod
    def _get_ballot(ballots_dir: str, filename: str) -> PlaintextBallot:
        full_file = join(ballots_dir, filename)
        echo(f"importing {filename}")
        return from_file(PlaintextBallot, full_file)
