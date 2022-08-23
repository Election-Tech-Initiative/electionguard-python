from enum import Enum

from .utils import space_between_capitals


class ProofUsage(Enum):
    """Usage case for proof"""

    Unknown = "Unknown"
    SecretValue = "Prove knowledge of secret value"
    ConstantValue = "Prove value is a given constant"
    RangeValue = "Prove value is within a given range (0, 1, ..., or limit)"
    BinaryValue = "Prove value is binary (0 or 1)"


class Proof:
    """Base class for proofs with name and usage case"""

    name: str = "Proof"
    usage: ProofUsage = ProofUsage.Unknown

    def __init__(self) -> None:
        object.__setattr__(
            self, "name", space_between_capitals(self.__class__.__name__)
        )
