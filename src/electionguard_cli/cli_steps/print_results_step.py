from typing import Dict
from electionguard.manifest import Manifest
from electionguard.type import BallotId
from electionguard.tally import (
    PlaintextTally,
)

from ..cli_models import CliDecryptResults
from .cli_step_base import CliStepBase


class PrintResultsStep(CliStepBase):
    """Responsible for printing the results of an end-to-end election."""

    def _print_tally(
        self,
        plaintext_tally: PlaintextTally,
        manifest: Manifest,
        selection_names: Dict[str, str],
    ) -> None:
        self.print_header("Decrypted tally")
        for tally_contest in plaintext_tally.contests.values():
            contest_name = PrintResultsStep._get_contest_name(
                manifest, tally_contest.object_id
            )
            self.print_value("Contest", contest_name)
            for selection in tally_contest.selections.values():
                name = selection_names[selection.object_id]
                self.print_value(f"  {name}", selection.tally)

    @staticmethod
    def _get_contest_name(manifest: Manifest, contest_id: str) -> str:
        matching_contests = (c for c in manifest.contests if c.object_id == contest_id)
        contest = next(matching_contests, None)
        return contest_id if contest is None else contest.name

    def _print_spoiled_ballots(
        self,
        plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally],
        manifest: Manifest,
        selection_names: Dict[str, str],
    ) -> None:
        ballot_ids = plaintext_spoiled_ballots.keys()
        for ballot_id in ballot_ids:
            self.print_header(f"Spoiled ballot '{ballot_id}'")
            spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
            for contest in spoiled_ballot.contests.values():
                contest_name = self._get_contest_name(manifest, contest.object_id)
                self.print_value("Contest", contest_name)
                for selection in contest.selections.values():
                    name = selection_names[selection.object_id]
                    self.print_value(f"  {name}", selection.tally)

    def print_election_results(
        self, decrypt_results: CliDecryptResults, manifest: Manifest
    ) -> None:
        selection_names = manifest.get_selection_names("en")
        self._print_tally(decrypt_results.plaintext_tally, manifest, selection_names)
        self._print_spoiled_ballots(
            decrypt_results.plaintext_spoiled_ballots, manifest, selection_names
        )
