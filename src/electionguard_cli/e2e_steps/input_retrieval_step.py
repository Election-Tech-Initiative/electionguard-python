from io import TextIOWrapper
from typing import List, Optional

from electionguard.ballot import PlaintextBallot
from electionguard.guardian import Guardian
from electionguard.manifest import InternationalizedText, Manifest
from electionguard.serialize import from_file_wrapper, from_list_in_file_wrapper

from ..cli_models.e2e_inputs import E2eInputs
from .e2e_step_base import E2eStepBase


class InputRetrievalStep(E2eStepBase):
    """Responsible for retrieving and displaying user provided inputs."""

    def get_inputs(
        self,
        guardian_count: int,
        quorum: int,
        manifest_file: TextIOWrapper,
        ballots_file: TextIOWrapper,
        spoil_id: str,
        output_path: str,
    ) -> E2eInputs:
        self.print_header("Retrieving Inputs")
        guardians = InputRetrievalStep._get_guardians(guardian_count, quorum)
        manifest: Manifest = self._get_manifest(manifest_file)
        ballots = InputRetrievalStep._get_ballots(ballots_file)
        self.print_value("Guardians", guardian_count)
        self.print_value("Quorum", quorum)
        return E2eInputs(
            guardian_count, quorum, guardians, manifest, ballots, spoil_id, output_path
        )

    @staticmethod
    def _get_ballots(ballots_file: TextIOWrapper) -> List[PlaintextBallot]:
        ballots: List[PlaintextBallot] = from_list_in_file_wrapper(
            PlaintextBallot, ballots_file
        )
        return ballots

    def print_manifest(self, manifest: Manifest) -> None:
        def get_first_value(text: Optional[InternationalizedText]) -> str:
            return "" if text is None else text.text[0].value

        manifest_name = get_first_value(manifest.name)
        self.print_value("Name", manifest_name)
        self.print_value("Scope", manifest.election_scope_id)
        self.print_value("Geopolitical Units", len(manifest.geopolitical_units))
        self.print_value("Parties", len(manifest.parties))
        self.print_value("Candidates", len(manifest.candidates))
        self.print_value("Contests", len(manifest.contests))
        self.print_value("Ballot Styles", len(manifest.ballot_styles))

    def _get_manifest(self, manifest_file: TextIOWrapper) -> Manifest:
        self.print_header("Retrieving manifest")
        manifest: Manifest = from_file_wrapper(Manifest, manifest_file)
        if not manifest.is_valid():
            raise ValueError("manifest file is invalid")
        self.print_manifest(manifest)
        return manifest

    @staticmethod
    def _get_guardians(number_of_guardians: int, quorum: int) -> List[Guardian]:
        guardians: List[Guardian] = []
        for i in range(number_of_guardians):
            guardians.append(
                Guardian(
                    str(i + 1),
                    i + 1,
                    number_of_guardians,
                    quorum,
                )
            )
        return guardians
