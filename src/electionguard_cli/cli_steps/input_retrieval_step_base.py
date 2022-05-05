from click import echo
from typing import Optional, List
from os.path import isfile, isdir, join
from os import listdir
from click import echo
from io import TextIOWrapper
from electionguard.election import CiphertextElectionContext

from electionguard.ballot import PlaintextBallot
from electionguard.manifest import InternationalizedText, Manifest
from electionguard.serialize import from_list_in_file, from_file
from electionguard.serialize import (
    from_file_wrapper,
)

from .cli_step_base import CliStepBase


class InputRetrievalStepBase(CliStepBase):
    """A common base class for all CLI commands that accept user input"""

    def _get_manifest(self, manifest_file: TextIOWrapper) -> Manifest:
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
    def _get_context(context_file: TextIOWrapper) -> CiphertextElectionContext:
        return from_file_wrapper(CiphertextElectionContext, context_file)

    @staticmethod
    def _get_ballots(ballots_path: str) -> List[PlaintextBallot]:
        if isfile(ballots_path):
            return from_list_in_file(PlaintextBallot, ballots_path)
        if isdir(ballots_path):
            files = listdir(ballots_path)
            return [InputRetrievalStepBase._get_ballot(ballots_path, f) for f in files]
        raise ValueError(
            f"{ballots_path} is neither a valid file nor a valid directory"
        )

    @staticmethod
    def _get_ballot(ballots_dir: str, filename: str) -> PlaintextBallot:
        full_file = join(ballots_dir, filename)
        echo(f"Importing {filename}")
        return from_file(PlaintextBallot, full_file)
