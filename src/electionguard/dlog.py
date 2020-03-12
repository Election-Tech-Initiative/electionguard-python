# support for computing discrete logs, with a cache so they're never recomputed

from typing import Dict

from .group import G, ElementModP, ONE_MOD_P, mult_mod_p

__dlog_cache: Dict[ElementModP, int] = {ONE_MOD_P: 0}
__dlog_max_elem = ONE_MOD_P
__dlog_max_exp = 0


def discrete_log(e: ElementModP) -> int:
    """
    Computes the discrete log (base g, mod p) of the given element,
    with internal caching of results. The exponent is expected
    to fit within [0, Q).
    """

    global __dlog_cache
    global __dlog_max_elem
    global __dlog_max_exp

    g = ElementModP(G)

    if e in __dlog_cache:
        return __dlog_cache[e]

    while e != __dlog_max_elem:
        __dlog_max_exp = __dlog_max_exp + 1
        __dlog_max_elem = mult_mod_p(g, __dlog_max_elem)
        __dlog_cache[__dlog_max_elem] = __dlog_max_exp

    return __dlog_cache[__dlog_max_elem]
