# pylint: disable=global-statement
# support for computing discrete logs, with a cache so they're never recomputed

import asyncio
from functools import lru_cache
from math import isqrt

from .constants import get_generator
from .singleton import Singleton
from .group import BaseElement, ElementModP, ONE_MOD_P, mult_inv_p, mult_p, pow_p

DiscreteLogCache = dict[ElementModP, int]

_DLOG_MAX_EXPONENT = 100_000_000
"""The max exponent to calculate.  This value is used to stop a race condition."""

_MAX_CACHE_FILL = 100_000
"""The most steps to walk and cache on the way to a value. Beyond this, only the value is cached."""

_INITIAL_CACHE = {ONE_MOD_P: 0}


class DiscreteLogExponentError(ValueError):
    """Raised when the max exponent is larger than the system allows."""

    def __init__(
        self,
        exponent: int,
        max_exponent: int = _DLOG_MAX_EXPONENT,
        message: str | None = None,
    ) -> None:
        super().__init__(
            message
            or f"Discrete log exponent of {exponent} exceeds maximum of {max_exponent}."
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
) -> tuple[int, DiscreteLogCache]:
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
) -> tuple[int, DiscreteLogCache]:
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
    max_exponent: int, cache: DiscreteLogCache | None = None
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


@lru_cache(maxsize=4)
def _get_baby_steps(generator: int, step_count: int) -> dict[ElementModP, int]:
    """Map g^j to j for every j below step_count, keeping the smallest j of a repeat."""
    g = ElementModP(generator, False)
    baby_steps: dict[ElementModP, int] = {}
    current_element = ONE_MOD_P
    for exponent in range(step_count):
        baby_steps.setdefault(current_element, exponent)
        current_element = mult_p(g, current_element)
    return baby_steps


def _find_exponent(element: ElementModP, max_exponent: int) -> int | None:
    """
    Find the smallest x up to max_exponent with element = g^x, using baby-step
    giant-step, or None if there is none. This takes about 2 * sqrt(max_exponent)
    multiplications and stores nothing in the cache, so a value with no small exponent
    (a wrong key or a corrupted ciphertext) fails at once and a large one costs no memory.
    """
    step_count = isqrt(max_exponent) + 1
    baby_steps = _get_baby_steps(get_generator(), step_count)
    giant_step = mult_inv_p(pow_p(ElementModP(get_generator(), False), step_count))

    current_element = element
    for giant_exponent in range(step_count):
        baby_exponent = baby_steps.get(current_element)
        if baby_exponent is not None:
            exponent = giant_exponent * step_count + baby_exponent
            return exponent if exponent <= max_exponent else None
        current_element = mult_p(current_element, giant_step)
    return None


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
    element_exponent = _find_exponent(element, max_exponent)
    if element_exponent is None:
        raise DiscreteLogExponentError(
            max_exponent + 1,
            max_exponent,
            f"Value is not g^x for any x up to {max_exponent}: "
            "a wrong key, corrupted data, or a count above the maximum.",
        )
    if not 0 < element_exponent - exponent <= _MAX_CACHE_FILL:
        cache[element] = element_exponent
        return cache

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
        exponent = min(exponent, self._max_exponent)

        precompute_discrete_log_cache(exponent, self._cache)

    async def precompute_cache_async(self, exponent: int) -> None:
        exponent = min(exponent, self._max_exponent)

        async with self._mutex:
            precompute_discrete_log_cache(exponent, self._cache)

    def discrete_log(self, element: ElementModP) -> int:
        result, _cache = compute_discrete_log(
            element, self._cache, self._max_exponent, self._lazy_evaluation
        )
        return result

    async def discrete_log_async(self, element: ElementModP) -> int:
        result, _cache = await compute_discrete_log_async(
            element, self._cache, self._mutex, self._max_exponent, self._lazy_evaluation
        )
        return result
