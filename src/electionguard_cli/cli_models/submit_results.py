from electionguard.ballot import SubmittedBallot


class SubmitResults:
    """Responsible for holding the results of submitting ballots in an election."""

    def __init__(
        self,
        submitted_ballots: list[SubmittedBallot],
    ):
        self.submitted_ballots = submitted_ballots

    submitted_ballots: list[SubmittedBallot]
