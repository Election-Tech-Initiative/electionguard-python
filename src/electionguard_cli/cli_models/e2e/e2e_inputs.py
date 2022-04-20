from typing import List
from electionguard.ballot import PlaintextBallot
from ..shared.cli_election_inputs_base import CliElectionInputsBase


class E2eInputs(CliElectionInputsBase):
    """Responsible for holding the inputs for the CLI's e2e command."""

    ballots: List[PlaintextBallot]
    spoil_id: str
    output_record: str
    output_keys: str
