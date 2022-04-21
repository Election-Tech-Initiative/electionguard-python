from typing import List
from electionguard.ballot import PlaintextBallot
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest
from electionguard_cli.cli_models.shared.cli_election_inputs_base import (
    CliElectionInputsBase,
)


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
        output_record: str,
        output_keys: str,
    ):
        self.guardian_count = guardian_count
        self.quorum = quorum
        self.guardians = guardians
        self.manifest = manifest
        self.ballots = ballots
        self.spoil_id = spoil_id
        self.output_record = output_record
        self.output_keys = output_keys

    ballots: List[PlaintextBallot]
    spoil_id: str
    output_record: str
    output_keys: str
