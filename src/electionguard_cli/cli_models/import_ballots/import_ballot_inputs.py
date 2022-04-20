from typing import List
from electionguard.ballot import SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest
from ..shared.cli_election_inputs_base import CliElectionInputsBase


class ImportBallotInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's import ballots command"""

    def __init__(
        self,
        guardian_count: int,
        quorum: int,
        guardians: List[Guardian],
        manifest: Manifest,
        submitted_ballots: List[SubmittedBallot],
        context: CiphertextElectionContext,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.submitted_ballots = submitted_ballots
        self.context = context

    submitted_ballots: List[SubmittedBallot]
    context: CiphertextElectionContext
