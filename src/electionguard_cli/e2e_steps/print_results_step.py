from typing import Dict
import click
from electionguard_cli.cli_models import E2eDecryptResults
from electionguard.type import BallotId
from electionguard.tally import (
    PlaintextTally,
)
from electionguard_cli.e2e_steps.shared.input_retrieval_step_base import (
    InputRetrievalStepBase,
)

from ..cli_models import E2eDecryptResults, E2eInputs
from .e2e_step_base import E2eStepBase


class PrintResultsStep(E2eStepBase):
    """Responsible for printing the results of an end-to-end election."""

    def _print_tally(self, plaintext_tally: PlaintextTally) -> None:
        self.print_header("Decrypted tally")
        for contest in plaintext_tally.contests.values():
            click.echo(f"Contest: {contest.object_id}")
            for selection in contest.selections.values():
                self.print_value(f"  {selection.object_id}", f"{selection.tally} votes")

    def _print_spoiled_ballots(
        self,
        plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally],
    ) -> None:
        ballot_ids = plaintext_spoiled_ballots.keys()
        for ballot_id in ballot_ids:
            self.print_header(f"Spoiled ballot '{ballot_id}'")
            spoiled_ballot = plaintext_spoiled_ballots[ballot_id]
            for contest in spoiled_ballot.contests.values():
                click.echo(f"Contest: {contest.object_id}")
                for selection in contest.selections.values():
                    self.print_value(
                        f"  {selection.object_id}", f"{selection.tally} votes"
                    )

    def print_election_results(
        self,
        decrypt_results: E2eDecryptResults,
    ) -> None:
        self._print_tally(decrypt_results.plaintext_tally)
        self._print_spoiled_ballots(decrypt_results.plaintext_spoiled_ballots)
