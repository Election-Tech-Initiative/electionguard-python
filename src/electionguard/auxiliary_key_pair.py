from typing import Callable, NamedTuple


class AuxiliaryKeyPair(NamedTuple):
    """A tuple of a secret key and public key."""

    secret_key: str
    """The secret or private key"""
    public_key: str


AuxiliaryEncrypt = Callable[[str, AuxiliaryKeyPair], str]

AuxiliaryDecrypt = Callable[[str, AuxiliaryKeyPair], str]
