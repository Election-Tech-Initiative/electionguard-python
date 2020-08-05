# support for computing discrete logs, with a cache so they're never recomputed

import asyncio
from typing import Dict, Optional

from .group import G, ElementModP, ONE_MOD_P, mult_p, int_to_p_unchecked

__dlog_cache: Dict[ElementModP, int] = {ONE_MOD_P: 0}
__dlog_max_elem = ONE_MOD_P
__dlog_max_exp = 0

__dlog_lock: Optional[asyncio.Lock] = None


def discrete_log(e: ElementModP) -> int:
    """
    Computes the discrete log (base g, mod p) of the given element,
    with internal caching of results. Should run efficiently when called
    multiple times when the exponent is at most in the single-digit millions.
    Performance will degrade if it's much larger.

    Note: *this function is thread-safe*. For the best possible performance,
    pre-compute the discrete log of a number you expect to have the biggest
    exponent you'll ever see. After that, the cache will be fully loaded,
    and every call will be nothing more than a dictionary lookup.
    """
    global __dlog_cache

    # no need for mutually exclusive access when reading from the cache
    if e in __dlog_cache:
        return __dlog_cache[e]
    else:
        return asyncio.run(__discrete_log_internal(e))


async def __discrete_log_internal(e: ElementModP) -> int:
    global __dlog_cache
    global __dlog_max_elem
    global __dlog_max_exp
    global __dlog_lock

    if __dlog_lock is None:
        # Initialize the lock on on first function call per process
        __dlog_lock = asyncio.Lock()

    async with __dlog_lock:
        g = int_to_p_unchecked(G)
        while e != __dlog_max_elem:
            __dlog_max_exp = __dlog_max_exp + 1
            __dlog_max_elem = mult_p(g, __dlog_max_elem)
            __dlog_cache[__dlog_max_elem] = __dlog_max_exp

        return __dlog_cache[__dlog_max_elem]
