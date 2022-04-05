# pylint: disable=global-statement
# support for computing discrete logs, with a cache so they're never recomputed

import asyncio
from typing import Dict, Tuple

from .constants import get_generator
from .singleton import Singleton
from .group import BaseElement, ElementModP, ONE_MOD_P, mult_p

DiscreteLogCache = Dict[ElementModP, int]

_DLOG_MAX_EXPONENT = 100_000_000
"""The max exponent to calculate.  This value is used to stop a race condition."""

_INITIAL_CACHE = {ONE_MOD_P: 0}


class DiscreteLogExponentError(ValueError):
    """Raised when the max exponent is larger than the system allows."""

    def __init__(self, exponent: int, max_exponent: int = _DLOG_MAX_EXPONENT) -> None:
        super().__init__(
            f"Discrete log exponent of {exponent} exceeds maximum of {max_exponent}."
        )


class DiscreteLogNotFoundError(ValueError):
    """Raised when the discrete value could not be found in cache."""

    def __init__(self, element: BaseElement) -> None:
        super().__init__(f"Discrete log of {element} could not be found in cache.")


def compute_discrete_log(
    element: ElementModP,
    cache: DiscreteLogCache,
    max_exponent: int = _DLOG_MAX_EXPONENT,
    lazy_evaluation: bool = True,
) -> Tuple[int, DiscreteLogCache]:
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
    if not lazy_evaluation:
        raise DiscreteLogNotFoundError(element)

    _cache = compute_discrete_log_cache(element, cache, max_exponent)
    return (_cache[element], _cache)


async def compute_discrete_log_async(
    element: ElementModP,
    cache: DiscreteLogCache,
    mutex: asyncio.Lock = asyncio.Lock(),
    max_exponent: int = _DLOG_MAX_EXPONENT,
    lazy_evaluation: bool = True,
) -> Tuple[int, DiscreteLogCache]:
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
        if not lazy_evaluation:
            raise DiscreteLogNotFoundError(element)

        _cache = compute_discrete_log_cache(element, cache, max_exponent)
        return (_cache[element], _cache)


def precompute_discrete_log_cache(
    max_exponent: int, cache: DiscreteLogCache = None
) -> DiscreteLogCache:
    """
    Precompute the discrete log by the max exponent.
    """

    if max_exponent > _DLOG_MAX_EXPONENT:
        raise DiscreteLogExponentError(max_exponent)

    if not cache:
        cache = _INITIAL_CACHE

    current_element = list(cache)[-1]
    prev_exponent = cache[current_element]

    if prev_exponent >= max_exponent:
        return cache

    g = ElementModP(get_generator(), False)

    for exponent in range(prev_exponent + 1, max_exponent + 1):
        current_element = mult_p(g, current_element)
        cache[current_element] = exponent

    return cache


def compute_discrete_log_cache(
    element: ElementModP,
    cache: DiscreteLogCache,
    max_exponent: int = _DLOG_MAX_EXPONENT,
) -> DiscreteLogCache:
    """
    Compute or lazy evaluation a discrete log cache up to the specified element.
    """

    if max_exponent > _DLOG_MAX_EXPONENT:
        raise DiscreteLogExponentError(max_exponent)

    if not cache:
        cache = _INITIAL_CACHE

    max_element = list(cache)[-1]
    exponent = cache[max_element]
    if exponent > max_exponent:
        raise DiscreteLogExponentError(exponent, max_exponent)

    g = ElementModP(get_generator(), False)

    while element != max_element:
        exponent = exponent + 1
        if exponent > max_exponent:
            raise DiscreteLogExponentError(exponent, max_exponent)
        max_element = mult_p(g, max_element)
        cache[max_element] = exponent
    return cache


class DiscreteLog(Singleton):
    """
    A class instance of the discrete log that includes a cache.
    """

    _cache: DiscreteLogCache = {ONE_MOD_P: 0}
    _mutex = asyncio.Lock()
    _max_exponent: int = _DLOG_MAX_EXPONENT
    _lazy_evaluation: bool = True

    def get_cache(self) -> DiscreteLogCache:
        return self._cache

    def set_max_exponent(self, max_exponent: int) -> None:
        self._max_exponent = max_exponent

    def set_lazy_evaluation(self, lazy_evaluation: bool) -> None:
        self._lazy_evaluation = lazy_evaluation

    def precompute_cache(self, exponent: int) -> None:
        if exponent > self._max_exponent:
            exponent = self._max_exponent

        precompute_discrete_log_cache(exponent, self._cache)

    async def precompute_cache_async(self, exponent: int) -> None:
        if exponent > self._max_exponent:
            exponent = self._max_exponent

        async with self._mutex:
            precompute_discrete_log_cache(exponent)

    def discrete_log(self, element: ElementModP) -> int:
        (result, _cache) = compute_discrete_log(
            element, self._cache, self._max_exponent, self._lazy_evaluation
        )
        return result

    async def discrete_log_async(self, element: ElementModP) -> int:
        (result, _cache) = await compute_discrete_log_async(
            element, self._cache, self._mutex, self._max_exponent, self._lazy_evaluation
        )
        return result
