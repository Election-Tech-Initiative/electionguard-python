from typing import List
from electionguard.ballot import SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest
from electionguard_cli.cli_models.shared.cli_election_inputs_base import (
    CliElectionInputsBase,
)


class ImportBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's import ballots command"""

    def __init__(
        self,
        guardians: List[Guardian],
        manifest: Manifest,
        submitted_ballots: List[SubmittedBallot],
        context: CiphertextElectionContext,
    ):
        self.guardian_count = context.number_of_guardians
        self.quorum = context.quorum
        self.guardians = guardians
        self.manifest = manifest
        self.submitted_ballots = submitted_ballots
        self.context = context

    submitted_ballots: List[SubmittedBallot]
    context: CiphertextElectionContext
