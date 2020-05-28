from abc import abstractmethod
from hashlib import sha256
from typing import (
    Union,
    Optional,
    Protocol,
    runtime_checkable,
    Sequence,
)

from .group import (
    ElementModPOrQ,
    ElementModQ,
    Q_MINUS_ONE,
    int_to_q_unchecked,
    ElementModP,
)


@runtime_checkable
class CryptoHashable(Protocol):
    @abstractmethod
    def crypto_hash(self) -> ElementModQ:
        """
        Generates a hash given the fields on the implementing instance.
        """
        ...


@runtime_checkable
class CryptoHashCheckable(Protocol):
    @abstractmethod
    def crypto_hash_with(self, seed_hash: ElementModQ) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...


CRYPTO_HASHABLE_T = Union[CryptoHashable, ElementModPOrQ, str, int]
CRYPTO_HASHABLE_ALL = Union[
    CRYPTO_HASHABLE_T,
    Sequence[CRYPTO_HASHABLE_T],
    Optional[CRYPTO_HASHABLE_T],
    Optional[Sequence[CRYPTO_HASHABLE_T]],
]


def hash_elems(*a: CRYPTO_HASHABLE_ALL) -> ElementModQ:
    """
    Given zero or more elements, calculate their cryptographic hash
    using SHA256. Allowed element types are `ElementModP`, `ElementModQ`,
    `str`, or `int`, anything implementing `CryptoHashable`, and lists
    or optionals of any of those types.

    :param a: Zero or more elements of any of the accepted types.
    :return: A cryptographic hash of these elements, concatenated.
    """
    h = sha256()
    h.update("|".encode("utf-8"))
    for x in a:
        # We could just use str(x) for everything, but then we'd have a resulting string
        # that's a bit Python-specific, and we'd rather make it easier for other languages
        # to exactly match this hash function.

        if not x:
            # This case captures empty lists and None, nicely guaranteeing that we don't
            # need to do a recursive call if the list is empty. So we need a string to
            # feed in for both of these cases. "None" would be a Python-specific thing,
            # so we'll go with the more JSON-ish "null".
            hash_me = "null"

        elif isinstance(x, list):
            # The simplest way to deal with lists is to crunch them recursively.
            hash_me = str(hash_elems(*x).to_int())

        elif isinstance(x, ElementModP) or isinstance(x, ElementModQ):
            hash_me = str(x.to_int())
        elif isinstance(x, CryptoHashable):
            hash_me = str(x.crypto_hash().to_int())
        else:
            hash_me = str(x)
        h.update((hash_me + "|").encode("utf-8"))

    # Note: the returned value will range from [1,Q), because zeros are bad
    # for some of the nonces. (g^0 == 1, which would be an unhelpful thing
    # to multiply something with, if you were trying to encrypt it.)

    # Also, we don't need the checked version of int_to_q, because the
    # modulo operation here guarantees that we're in bounds.
    return int_to_q_unchecked(
        1 + (int.from_bytes(h.digest(), byteorder="big") % Q_MINUS_ONE)
    )
