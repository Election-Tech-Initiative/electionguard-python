from typing import Callable, Optional, NamedTuple

from .types import GUARDIAN_ID

MESSAGE = str
AUXILIARY_PUBLIC_KEY = str
AUXILIARY_SECRET_KEY = str
ENCRYPTED_MESSAGE = str


class AuxiliaryPublicKey(NamedTuple):
    """A tuple of auxiliary public key and owner information that can be shared between guardians"""

    owner_id: GUARDIAN_ID
    """
    The unique identifier of the guardian owning the key
    """

    sequence_order: int
    """
    The sequence order of the auxiliary public key (usually the guardian's sequence order)
    """

    key: AUXILIARY_PUBLIC_KEY
    """
    A string representation of the Auxiliary public key that can be shared between guardians.
    It is up to the external `AuxiliaryEncrypt` function to know how to parse this value
    """


class AuxiliaryKeyPair(NamedTuple):
    """A tuple of a secret key and public key."""

    owner_id: GUARDIAN_ID
    """
    The unique identifier of the guardian owning the key
    """

    sequence_order: int
    """
    The sequence order of the auxiliary public key (usually the guardian's sequence order)
    """

    secret_key: AUXILIARY_SECRET_KEY
    """The secret or private key"""

    public_key: AUXILIARY_PUBLIC_KEY
    """
    A string representation of the Auxiliary public key that can be shared between guardians.
    It is up to the external `AuxiliaryEncrypt` function to know how to parse this value
    """

    def share(self) -> AuxiliaryPublicKey:
        """Share the auxiliary public key and associated data"""
        return AuxiliaryPublicKey(self.owner_id, self.sequence_order, self.public_key)


AuxiliaryEncrypt = Callable[
    [MESSAGE, AUXILIARY_PUBLIC_KEY], Optional[ENCRYPTED_MESSAGE]
]
"""A callable type that represents the auxiliary encryption scheme."""

AuxiliaryDecrypt = Callable[
    [ENCRYPTED_MESSAGE, AUXILIARY_SECRET_KEY], Optional[MESSAGE]
]
"""A callable type that represents the auxiliary decryption scheme."""
