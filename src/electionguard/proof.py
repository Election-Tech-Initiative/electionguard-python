from enum import Enum

from .serializable import Serializable
from .utils import space_between_capitals


class ProofUsage(Enum):
    """Usage case for proof"""

    Unknown = "Unknown"
    SecretValue = "Prove knowledge of secret value"
    SelectionLimit = "Prove value within selection's limit"
    SelectionValue = "Prove selection's value (0 or 1)"


class Proof(Serializable):
    """Base class for proofs with name and usage case"""

    name: str = "Proof"
    usage: ProofUsage = ProofUsage.Unknown

    def __init__(self) -> None:
        object.__setattr__(
            self, "name", space_between_capitals(self.__class__.__name__)
        )
