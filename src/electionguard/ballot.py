from dataclasses import dataclass, field
from typing import Optional

from typing import Optional, List

from .serializable import Serializable

from .is_valid import IsValid
from .chaum_pedersen import ConstantChaumPedersenProof, DisjunctiveChaumPedersenProof
from .elgamal import ElGamalCiphertext

from .election import Contest, Selection

@dataclass
class BallotSelection(Selection, IsValid):
    is_dummy_selection: Optional[bool] = field(default=None)
    plaintext: Optional[str] = field(default=None)
    message: Optional[ElGamalCiphertext] = field(default=None)
    crypto_hash: Optional[str] = field(default=None)
    proof: Optional[DisjunctiveChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:

        is_valid_ballot_in_state = self.is_dummy_selection is None \
            and self.plaintext is not None \
            and self.message is None \
            and self.crypto_hash is None \
            and self.proof is None

        is_valid_ballot_out_state = self.is_dummy_selection is not None \
            and self.plaintext is None \
            and self.message is not None \
            and self.crypto_hash is not None \
            and self.proof is not None

        # TODO: verify hash if not None
        # TODO: verify proof if not None
        return is_valid_ballot_in_state \
            or is_valid_ballot_out_state

@dataclass
class BallotContest(Contest, IsValid):
    ballot_selections: List[BallotSelection] = field(default_factory=lambda: [])
    crypto_hash: Optional[str] = field(default=None)
    proof: Optional[ConstantChaumPedersenProof] = field(default=None)

    def is_valid(self) -> bool:

        # TODO: raise super method
        selections_valid: List[bool] = list()
        for selection in self.ballot_selections:
            selections_valid.append(selection.is_valid())

        # TODO: verify hash if not None
        # TODO: verify proof if not None
        return all(selections_valid)

@dataclass
class Ballot(Serializable, IsValid):
    """
    """
    object_id: str
    ballot_style: str
    contests: List[BallotContest]
    crypto_hash: Optional[str] = field(default=None)
    tracking_id: Optional[str] = field(default=None)

    def is_valid(self) -> bool:
        """
        """
        contests_valid: List[bool] = list()
        for contest in self.contests:
            contests_valid.append(contest.is_valid())

        is_valid_in_state = self.tracking_id is None \
            and self.crypto_hash is None

        is_valid_out_state = self.tracking_id is not None \
            and self.crypto_hash is not None

        # TODO: verify hash if not None
        return (is_valid_in_state or is_valid_out_state) and all(contests_valid)
