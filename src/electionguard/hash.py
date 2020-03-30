from hashlib import sha256
from typing import Union

from .group import ElementModPOrQ, ElementModQ, Q_MINUS_ONE, int_to_q_unchecked


# TODO: decide how we want to represent the inputs to the hash functions. For now, converting them to
#   intermediary text strings generates consistent and predictable solutions. Adding punctuation
#   avoids misinterpretations. But is this the "best" way to go?


def hash_elems(*a: Union[ElementModPOrQ, str, int]) -> ElementModQ:
    """
    Given an array of elements, calculate their hash.
    Allowed types are ElementModP, ElementModQ, and str.

    :param a: An array of elements.
    :return: A hash of these elements, concatenated.
    """
    h = sha256()
    h.update("|".encode("utf-8"))
    for x in a:
        h.update((str(x) + "|").encode("utf-8"))

    # Note: the returned has will range from [1,Q), because zeros are bad
    # for some of the nonces. (g^0 == 1, which would be an unhelpful thing
    # to multiply something with, if you were trying to encrypt it.)

    # Also, we don't need the checked version of int_to_q, because the
    # modulo operation here guarantees that we're in bounds.
    return int_to_q_unchecked(1 + (int.from_bytes(h.digest(), byteorder='big') % Q_MINUS_ONE))
