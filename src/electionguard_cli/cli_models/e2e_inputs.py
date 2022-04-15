from abc import ABC
from typing import List
from electionguard.ballot import PlaintextBallot, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest


class CliElectionInputsBase(ABC):
    """Responsible for holding inputs common to all CLI election commands"""

    guardian_count: int
    quorum: int
    manifest: Manifest
    guardians: List[Guardian]


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


class E2eInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's e2e command."""

    def __init__(
        self,
        guardian_count: int,
        quorum: int,
        guardians: List[Guardian],
        manifest: Manifest,
        ballots: List[PlaintextBallot],
        spoil_id: str,
        output_file: str,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.ballots = ballots
        self.spoil_id = spoil_id
        self.output_file = output_file

    ballots: List[PlaintextBallot]
    spoil_id: str
    output_file: str
