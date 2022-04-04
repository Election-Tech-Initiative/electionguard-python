from typing import Dict
from electionguard.tally import PlaintextTally
from electionguard.type import BallotId

class E2eDecryptResults:
    """Responsible for holding the results of decrypting an election"""

    def __init__(self, plaintext_tally: PlaintextTally, plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]):
        self.plaintext_tally = plaintext_tally
        self.plaintext_spoiled_ballots = plaintext_spoiled_ballots

    plaintext_tally: PlaintextTally
    plaintext_spoiled_ballots: Dict[BallotId, PlaintextTally]