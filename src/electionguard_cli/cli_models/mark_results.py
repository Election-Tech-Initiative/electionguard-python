from typing import List
from electionguard.ballot import PlaintextBallot


class MarkResults:
    """Responsible for holding the results of marking ballots in an election."""

    def __init__(
        self,
        plaintext_ballots: List[PlaintextBallot],
    ):
        self.plaintext_ballots = plaintext_ballots

    plaintext_ballots: List[PlaintextBallot]
