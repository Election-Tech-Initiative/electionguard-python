# support for computing discrete logs, with a cache so they're never recomputed

from typing import Dict

from .group import ElementModQ, G, ZERO_MOD_Q, ElementModP, ONE_MOD_P, mult_mod_p

__dlog_cache: Dict[ElementModP, ElementModQ] = {ONE_MOD_P: ZERO_MOD_Q}
__dlog_max_elem = ONE_MOD_P
__dlog_max_exp = 0


def discrete_log(e: ElementModP) -> ElementModQ:
    """
    Computes the discrete log (base g) of the given element,
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
        __dlog_max_elem =  mult_mod_p(g, __dlog_max_elem)
        __dlog_cache[__dlog_max_elem] = ElementModQ(__dlog_max_exp)

    return __dlog_cache[__dlog_max_elem]

