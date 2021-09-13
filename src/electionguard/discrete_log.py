# pylint: disable=global-statement
# support for computing discrete logs, with a cache so they're never recomputed

import asyncio
from typing import Dict, Tuple

from .constants import get_generator
from .singleton import Singleton
from .group import ElementModP, ONE_MOD_P, mult_p

DLOG_CACHE = Dict[ElementModP, int]
DLOG_MAX = 100_000_000
"""The max number to calculate.  This value is used to stop a race condition."""


def compute_discrete_log(
    element: ElementModP, cache: DLOG_CACHE
) -> Tuple[int, DLOG_CACHE]:
    """
    Computes the discrete log (base g, mod p) of the given element,
    with internal caching of results. Should run efficiently when called
    multiple times when the exponent is at most in the single-digit millions.
    Performance will degrade if it's much larger.

    For the best possible performance,
    pre-compute the discrete log of a number you expect to have the biggest
    exponent you'll ever see. After that, the cache will be fully loaded,
    and every call will be nothing more than a dictionary lookup.
    """

    if element in cache:
        return (cache[element], cache)

    _cache = compute_discrete_log_cache(element, cache)
    return (_cache[element], _cache)


async def discrete_log_async(
    element: ElementModP,
    cache: DLOG_CACHE,
    mutex: asyncio.Lock = asyncio.Lock(),
) -> Tuple[int, DLOG_CACHE]:
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
    if element in cache:
        return (cache[element], cache)

    async with mutex:
        if element in cache:
            return (cache[element], cache)

        _cache = compute_discrete_log_cache(element, cache)
        return (_cache[element], _cache)


def compute_discrete_log_cache(
    element: ElementModP, cache: DLOG_CACHE
) -> Dict[ElementModP, int]:
    """
    Compute a discrete log cache up to the specified element.
    """
    if not cache:
        cache = {ONE_MOD_P: 0}
    max_element = list(cache)[-1]
    exponent = cache[max_element]

    g = ElementModP(get_generator(), False)
    while element != max_element:
        exponent = exponent + 1
        if exponent > DLOG_MAX:
            raise ValueError("size is larger than max.")
        max_element = mult_p(g, max_element)
        cache[max_element] = exponent
        print(f"max: {max_element}, exp: {exponent}")
    return cache


class DiscreteLog(Singleton):
    """
    A class instance of the discrete log that includes a cache.
    """

    _cache: DLOG_CACHE = {ONE_MOD_P: 0}
    _mutex = asyncio.Lock()

    def discrete_log(self, element: ElementModP) -> int:
        (result, cache) = compute_discrete_log(element, self._cache)
        self._cache = cache
        return result

    async def discrete_log_async(self, element: ElementModP) -> int:
        (result, cache) = await discrete_log_async(element, self._cache, self._mutex)
        self._cache = cache
        return result
