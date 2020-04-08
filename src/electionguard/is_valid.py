from typing import Protocol
from abc import abstractmethod

class IsValid(Protocol):
    """
    """
    @abstractmethod
    def is_valid(self) -> bool:
        ...