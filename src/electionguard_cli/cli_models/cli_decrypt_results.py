from dataclasses import dataclass
from typing import Dict
from electionguard.tally import CiphertextTally, PlaintextTally
from electionguard.type import BallotId
from electionguard.election_polynomial import LagrangeCoefficientsRecord


@dataclass
class CliDecryptResults:
    """Responsible for holding the results of decrypting an election."""

    plaintext_tally: PlaintextTally
    plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]
    ciphertext_tally: CiphertextTally
    lagrange_coefficients: LagrangeCoefficientsRecord
