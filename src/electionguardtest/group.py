from typing import Optional, TypeVar, Callable

from hypothesis.strategies import composite, integers, SearchStrategy

from electionguard.group import int_to_q, int_to_p, Q, P, ElementModQ, ElementModP

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def arb_element_mod_q(
    draw: _DrawType, elem=integers(min_value=0, max_value=Q - 1)
) -> Optional[ElementModQ]:
    """
    Generates an arbitrary element from [0,Q).
    """
    return int_to_q(draw(elem))


@composite
def arb_element_mod_q_no_zero(
    draw: _DrawType, elem=integers(min_value=1, max_value=Q - 1)
) -> Optional[ElementModQ]:
    """
    Generates an arbitrary element from [1,Q).
    """
    return int_to_q(draw(elem))


@composite
def arb_element_mod_p(
    draw: _DrawType, elem=integers(min_value=0, max_value=P - 1)
) -> Optional[ElementModP]:
    """
    Generates an arbitrary element from [0,P).
    """
    return int_to_p(draw(elem))


@composite
def arb_element_mod_p_no_zero(
    draw: _DrawType, elem=integers(min_value=1, max_value=P - 1)
) -> Optional[ElementModP]:
    """
    Generates an arbitrary element from [1,P).
    """
    return int_to_p(draw(elem))
