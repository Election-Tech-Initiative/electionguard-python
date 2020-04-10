from hashlib import sha256
from typing import Union

from .group import (
    ElementModPOrQ,
    ElementModQ,
    Q_MINUS_ONE,
    int_to_q_unchecked,
    ElementModP,
)


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
