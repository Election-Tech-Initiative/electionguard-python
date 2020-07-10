from typing import TypeVar, Callable

from hypothesis.strategies import composite, SearchStrategy

from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.group import ONE_MOD_Q, TWO_MOD_Q
from electionguardtest.group import elements_mod_q_no_zero

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def elgamal_keypairs(draw: _DrawType):
    """
    Generates an arbitrary ElGamal secret/public keypair.

    :param draw: Hidden argument, used by Hypothesis.
    """
    e = draw(elements_mod_q_no_zero())
    return elgamal_keypair_from_secret(e if e != ONE_MOD_Q else TWO_MOD_Q)
