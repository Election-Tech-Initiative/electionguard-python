from typing import Protocol, runtime_checkable
from abc import abstractmethod

from .group import ElementModP, ElementModQ
from .hash import CryptoHashable

@runtime_checkable
class IsValid(Protocol):
    """
    """
    @abstractmethod
    def is_valid(self) -> bool:
        ...

@runtime_checkable
class IsValidEncryption(Protocol):
    """
    """
    @abstractmethod
    def is_valid_encryption(self, seed_hash: ElementModQ, elgamal_public_key: ElementModP) -> bool:
        ...