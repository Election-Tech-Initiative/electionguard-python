from typing import TypeVar, Callable, Optional

from hypothesis.strategies import composite, SearchStrategy

from electionguard.elgamal import elgamal_keypair_from_secret, ElGamalKeyPair
from electionguard.group import ONE_MOD_Q, TWO_MOD_Q
from electionguardtest.group import arb_element_mod_q_no_zero

_T = TypeVar("_T")
_DrawType = Callable[[SearchStrategy[_T]], _T]


@composite
def arb_elgamal_keypair(draw: _DrawType, elem=arb_element_mod_q_no_zero()):
    """
    Generates an arbitrary ElGamal secret/public keypair.
    """
    e = draw(elem)
    return elgamal_keypair_from_secret(e if e != ONE_MOD_Q else TWO_MOD_Q)
