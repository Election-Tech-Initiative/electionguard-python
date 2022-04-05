from typing import Dict
import click

from electionguard.type import BallotId
from electionguard.tally import (
    PlaintextTally,
)

from ..cli_models import E2eDecryptResults
from .e2e_step_base import E2eStepBase


class PrintResultsStep(E2eStepBase):
    """Responsible for printing the results of an end-to-end election"""

    def print_tally(self, plaintext_tally: PlaintextTally) -> None:
        self.print_header("Decrypted tally")
        for contest in plaintext_tally.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                self.print_value(f"  {selection.object_id}", f"{selection.tally} votes")

    def print_spoiled_ballot(
        self, plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]
    ) -> None:
        ballot_id = list(plaintext_spoiled_ballots)[0]
        self.print_header(f"Spoiled ballot '{ballot_id}'")
        spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
        for contest in spoiled_ballot.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                self.print_value(f"  {selection.object_id}", f"{selection.tally} votes")

    def print_election_results(self, decrypt_results: E2eDecryptResults) -> None:
        self.print_tally(decrypt_results.plaintext_tally)
        self.print_spoiled_ballot(decrypt_results.plaintext_spoiled_ballots)
