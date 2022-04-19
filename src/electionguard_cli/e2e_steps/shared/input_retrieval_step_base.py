from io import TextIOWrapper
from typing import List, Optional
from electionguard.group import ElementModQ

from electionguard.guardian import Guardian
from electionguard.manifest import InternationalizedText, Manifest
from electionguard.serialize import (
    from_file_wrapper,
)
from electionguard_cli.e2e_steps.e2e_step_base import E2eStepBase


class InputRetrievalStepBase(E2eStepBase):
    """A common base class for all CLI commands that accept user input"""

    def _get_manifest(self, manifest_file: TextIOWrapper) -> Manifest:
        self.print_header("Retrieving manifest")
        manifest: Manifest = from_file_wrapper(Manifest, manifest_file)
        if not manifest.is_valid():
            raise ValueError("manifest file is invalid")
        self.__print_manifest(manifest)
        return manifest

    def __print_manifest(self, manifest: Manifest) -> None:
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

    @staticmethod
    def _get_guardians(number_of_guardians: int, quorum: int) -> List[Guardian]:
        guardians: List[Guardian] = []
        for i in range(number_of_guardians):
            guardians.append(
                Guardian.from_nonce(str(i + 1), i + 1, number_of_guardians, quorum)
            )
        return guardians
