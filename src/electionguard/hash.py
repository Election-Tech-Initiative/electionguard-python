# pylint: disable=isinstance-second-argument-not-valid-type
from abc import abstractmethod
from collections.abc import Sequence
from hashlib import sha256
from typing import (
    Iterable,
    List,
    Union,
    Protocol,
    runtime_checkable,
    Sequence as TypedSequence,
)

from .constants import get_small_prime
from .utils import BYTE_ENCODING, BYTE_ORDER
from .group import (
    ElementModPOrQ,
    ElementModQ,
    ElementModP,
)


@runtime_checkable
class CryptoHashable(Protocol):
    """
    Denotes hashable
    """

    @abstractmethod
    def crypto_hash(self) -> ElementModQ:
        """
        Generates a hash given the fields on the implementing instance.
        """


@runtime_checkable
class CryptoHashCheckable(Protocol):
    """
    Checkable version of crypto hash
    """

    @abstractmethod
    def crypto_hash_with(self, encryption_seed: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """


# All the "atomic" types that we know how to hash.
CryptoHashableT = Union[CryptoHashable, ElementModPOrQ, str, int, None]

# "Compound" types that we know how to hash. Note that we're using Sequence, rather than List,
# because Sequences are read-only, and thus safely covariant. All this really means is that
# we promise never to mutate any list that you pass to hash_elems.
CryptoHashableAll = Union[
    TypedSequence[CryptoHashableT],
    CryptoHashableT,
]


def hash_elems(*a: CryptoHashableAll) -> ElementModQ:
    """
    Given zero or more elements, calculate their cryptographic hash
    using SHA256. Allowed element types are `ElementModP`, `ElementModQ`,
    `str`, or `int`, anything implementing `CryptoHashable`, and lists
    or optionals of any of those types.

    :param a: Zero or more elements of any of the accepted types.
    :return: A cryptographic hash of these elements, concatenated.
    """
    h = sha256()
    h.update("|".encode(BYTE_ENCODING))
    for x in a:
        # We could just use str(x) for everything, but then we'd have a resulting string
        # that's a bit Python-specific, and we'd rather make it easier for other languages
        # to exactly match this hash function.

        if isinstance(x, (ElementModP, ElementModQ)):
            hash_me = x.to_hex()
        elif isinstance(x, CryptoHashable):
            hash_me = x.crypto_hash().to_hex()
        elif isinstance(x, str):
            # strings are iterable, so it's important to handle them before list-like types
            hash_me = x
        elif isinstance(x, int):
            hash_me = str(x)
        elif not x:
            # This case captures empty lists and None, nicely guaranteeing that we don't
            # need to do a recursive call if the list is empty. So we need a string to
            # feed in for both of these cases. "None" would be a Python-specific thing,
            # so we'll go with the more JSON-ish "null".
            hash_me = "null"
        elif isinstance(x, (Sequence, List, Iterable)):
            # The simplest way to deal with lists, tuples, and such are to crunch them recursively.
            hash_me = hash_elems(*x).to_hex()
        else:
            hash_me = str(x)

        h.update((hash_me + "|").encode(BYTE_ENCODING))

    return ElementModQ(
        int.from_bytes(h.digest(), byteorder=BYTE_ORDER) % get_small_prime()
    )
