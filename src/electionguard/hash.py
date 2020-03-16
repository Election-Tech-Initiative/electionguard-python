from .group import ElementModPOrQ, ElementModQ, Q
from hashlib import sha256

# TODO: decide how we want to represent the inputs to the hash functions. For now, converting them to
#   intermediary text strings generates consistent and predictable solutions. Adding punctuation
#   avoids misinterpretations. But is this the "best" way to go?


def hash_two_elems_mod_q(a: ElementModPOrQ, b: ElementModPOrQ) -> ElementModQ:
    """
    Given two elements, calculate their hash.
    :param a: Any element in P or Q
    :param b: Any element in P or Q
    :return: A hash of these two elements, concatenated.
    """
    h = sha256()
    h.update(str(a).encode("utf-8"))
    h.update(",".encode("utf-8"))
    h.update(str(b).encode("utf-8"))
    return ElementModQ(int.from_bytes(h.digest(), byteorder='big') % Q)
