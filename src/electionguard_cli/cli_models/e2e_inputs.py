from typing import List
from electionguard.ballot import PlaintextBallot
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest


class E2eInputs:
    """Responsible for holding the inputs to an end-to-end election."""

    def __init__(
        self,
        guardian_count: int,
        quorum: int,
        guardians: List[Guardian],
        manifest: Manifest,
        ballots: List[PlaintextBallot],
        spoil_id: str,
        output_path: str,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.ballots = ballots
        self.spoil_id = spoil_id
        self.output_path = output_path

    guardian_count: int
    quorum: int
    guardians: List[Guardian]
    manifest: Manifest
    ballots: List[PlaintextBallot]
    spoil_id: str
    output_path: str
