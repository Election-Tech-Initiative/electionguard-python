from typing import TypeVar, Callable

from hypothesis.strategies import composite, integers, SearchStrategy

from electionguard.constants import (
    get_small_prime,
    get_large_prime,
)
from electionguard.group import (
    ElementModP,
    ElementModQ,
)

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def elements_mod_q(draw: _DrawType) -> ElementModQ:
    """
    Generates an arbitrary element from [0,Q).

    :param draw: Hidden argument, used by Hypothesis.
    """
    return ElementModQ(draw(integers(min_value=0, max_value=get_small_prime() - 1)))


@composite
def elements_mod_q_no_zero(draw: _DrawType) -> ElementModQ:
    """
    Generates an arbitrary element from [1,Q).

    :param draw: Hidden argument, used by Hypothesis.
    """
    return ElementModQ(draw(integers(min_value=1, max_value=get_small_prime() - 1)))


@composite
def elements_mod_p(draw: _DrawType) -> ElementModP:
    """
    Generates an arbitrary element from [0,P).

    :param draw: Hidden argument, used by Hypothesis.
    """
    return ElementModP(draw(integers(min_value=0, max_value=get_large_prime() - 1)))


@composite
def elements_mod_p_no_zero(draw: _DrawType) -> ElementModP:
    """
    Generates an arbitrary element from [1,P).

    :param draw: Hidden argument, used by Hypothesis.
    """
    return ElementModP(draw(integers(min_value=1, max_value=get_large_prime() - 1)))
