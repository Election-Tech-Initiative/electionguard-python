from hashlib import sha256
from typing import Union

from .group import ElementModPOrQ, ElementModQ, Q, int_to_q


# TODO: decide how we want to represent the inputs to the hash functions. For now, converting them to
#   intermediary text strings generates consistent and predictable solutions. Adding punctuation
#   avoids misinterpretations. But is this the "best" way to go?


def hash_elems(*a: Union[ElementModPOrQ, str]) -> ElementModQ:
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
    return int_to_q(int.from_bytes(h.digest(), byteorder='big') % Q)
