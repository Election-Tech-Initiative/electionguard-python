from typing import Callable, Optional, NamedTuple

from .types import GUARDIAN_ID

MESSAGE = str
PUBLIC_KEY = str
SECRET_KEY = str
ENCRYPTED_MESSAGE = str


class AuxiliaryKeyPair(NamedTuple):
    """A tuple of a secret key and public key."""

    secret_key: SECRET_KEY
    """The secret or private key"""
    public_key: PUBLIC_KEY


class AuxiliaryPublicKey(NamedTuple):
    """A tuple of auxiliary public key and owner information"""

    owner_id: GUARDIAN_ID
    """
    The unique identifier of the guardian
    """

    sequence_order: int
    """
    The sequence order of the auxiliary public key (usually the guardian's sequence order)
    """

    key: PUBLIC_KEY
    """
    A string representation of the Auxiliary public key.  
    It is up to the external `AuxiliaryEncrypt` function to know how to parse this value
    """


AuxiliaryEncrypt = Callable[[MESSAGE, PUBLIC_KEY], Optional[ENCRYPTED_MESSAGE]]
"""A callable type that represents the auxiliary encryption scheme."""

AuxiliaryDecrypt = Callable[[ENCRYPTED_MESSAGE, SECRET_KEY], Optional[MESSAGE]]
"""A callable type that represents the auxiliary decryption scheme."""
