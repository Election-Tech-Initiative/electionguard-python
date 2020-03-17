from .group import ElementModPOrQ, ElementModQ, Q
from hashlib import sha256

# TODO: decide how we want to represent the inputs to the hash functions. For now, converting them to
#   intermediary text strings generates consistent and predictable solutions. Adding punctuation
#   avoids misinterpretations. But is this the "best" way to go?


def hash_elems(*a: ElementModPOrQ) -> ElementModQ:
    """
    Given an array of elements, calculate their hash.
    :param a: An array of elements in P or Q
    :return: A hash of these elements, concatenated.
    """
    h = sha256()
    h.update("|".encode("utf-8"))
    for x in a:
        h.update((str(x) + "|").encode("utf-8"))
    return ElementModQ(int.from_bytes(h.digest(), byteorder='big') % Q)
