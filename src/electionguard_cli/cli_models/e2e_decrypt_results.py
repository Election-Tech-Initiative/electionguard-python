from typing import Dict
from electionguard.tally import CiphertextTally, PlaintextTally
from electionguard.type import BallotId
from electionguard.election_polynomial import LagrangeCoefficientsRecord


class E2eDecryptResults:
    """Responsible for holding the results of decrypting an election."""

    def __init__(
        self,
        plaintext_tally: PlaintextTally,
        plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally],
        ciphertext_tally: CiphertextTally,
        lagrange_coefficients: LagrangeCoefficientsRecord,
    ):
        self.plaintext_tally = plaintext_tally
        self.plaintext_spoiled_ballots = plaintext_spoiled_ballots
        self.ciphertext_tally = ciphertext_tally
        self.lagrange_coefficients = lagrange_coefficients

    plaintext_tally: PlaintextTally
    plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]
    ciphertext_tally: CiphertextTally
    lagrange_coefficients: LagrangeCoefficientsRecord
