from dataclasses import dataclass
from typing import Callable, Optional

from .type import GuardianId

_Message = str
_AuxiliaryPublicKey = str
_AuxiliarySecretKey = str
_EncryptedMessage = str


@dataclass
class AuxiliaryPublicKey:
    """A tuple of auxiliary public key and owner information that can be shared between guardians"""

    owner_id: GuardianId
    """
    The unique identifier of the guardian owning the key
    """

    sequence_order: int
    """
    The sequence order of the auxiliary public key (usually the guardian's sequence order)
    """

    key: _AuxiliaryPublicKey
    """
    A string representation of the Auxiliary public key that can be shared between guardians.
    It is up to the external `AuxiliaryEncrypt` function to know how to parse this value
    """


@dataclass
class AuxiliaryKeyPair:
    """A tuple of a secret key and public key."""

    owner_id: GuardianId
    """
    The unique identifier of the guardian owning the key
    """

    sequence_order: int
    """
    The sequence order of the auxiliary public key (usually the guardian's sequence order)
    """

    secret_key: _AuxiliarySecretKey
    """The secret or private key"""

    public_key: _AuxiliaryPublicKey
    """
    A string representation of the Auxiliary public key that can be shared between guardians.
    It is up to the external `AuxiliaryEncrypt` function to know how to parse this value
    """

    def share(self) -> AuxiliaryPublicKey:
        """Share the auxiliary public key and associated data"""
        return AuxiliaryPublicKey(self.owner_id, self.sequence_order, self.public_key)


AuxiliaryEncrypt = Callable[
    [_Message, _AuxiliaryPublicKey], Optional[_EncryptedMessage]
]
"""A callable type that represents the auxiliary encryption scheme."""

AuxiliaryDecrypt = Callable[
    [_EncryptedMessage, _AuxiliarySecretKey], Optional[_Message]
]
"""A callable type that represents the auxiliary decryption scheme."""
