from hashlib import sha256
from typing import Iterable, List, Union, Optional, Protocol, runtime_checkable, TypeVar
from abc import abstractmethod

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
    def crypto_hash_with(self, seed_hash: Optional[ElementModQ] = None) -> ElementModQ:
        """
        Generates a hash with a given seed that can be checked later against the seed and class metadata.
        """
        ...

T = TypeVar("T", CryptoHashable, ElementModPOrQ, str, int)

# TODO: decide how we want to represent the inputs to the hash functions. For now, converting them to
#   intermediary text strings generates consistent and predictable solutions. Adding punctuation
#   avoids misinterpretations. But is this the "best" way to go?


def hash_elems(*a: Union[ElementModPOrQ, str, int]) -> ElementModQ:
    """
    Given one or more elements, calculate their cryptographic hash
    using SHA256. Allowed element types are `ElementModP`, `ElementModQ`,
    `str`, or `int`.

    :param a: An array of elements.
    :return: A cryptographic hash of these elements, concatenated.
    """
    h = sha256()
    h.update("|".encode("utf-8"))
    for x in a:
        # We could just use str(x) for everything, but then we'd have a resulting string
        # that's a bit Python-specific, and we'd rather make it easier for other languages
        # to exactly match this hash function.
        if isinstance(x, ElementModP) or isinstance(x, ElementModQ):
            hash_me = str(x.to_int())
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

def hashable_element(item: T) -> T:
    """
    if the item is `CryptoHashable` then unwrap the hash using the `crypto_hash` function
    :return: the unwrapped element
    """
    if isinstance(item, CryptoHashable):
        return item.crypto_hash()
    else:
        return item

def flatten(*args: Union[T, Optional[T], Optional[List[T]]]) -> Optional[List[T]]:
    """
    Flatten some arguments of mixed types into a single optional collection.  
    Supports optional parameters.
    :param *args: args conforming to T
    :return: a flat optional list of all of the elements passed in.
    """
    arguments: List[T] = []
    for item in args:
        if item:
            if isinstance(item, Iterable):
                for sub_item in item:
                    arguments.append(hashable_element(sub_item))
            else:
                arguments.append(hashable_element(item))
    if any(arguments):
        return arguments 
    else:
        return None
