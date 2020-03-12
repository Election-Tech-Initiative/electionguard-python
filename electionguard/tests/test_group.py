from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from electionguard.lib.group import P,Q,ElementModP,ElementModQ


@composite
def arb_element_mod_q(draw, elem=st.integers(min_value=0, max_value=Q-1)):
    return ElementModQ(draw(elem))

@composite
def arb_element_mod_q_no_zero(draw, elem=st.integers(min_value=1, max_value=Q-1)):
    return ElementModQ(draw(elem))

@composite
def arb_element_mod_p(draw, elem=st.integers(min_value=0, max_value=P-1)):
    return ElementModP(draw(elem))

@composite
def arb_element_mod_p_no_zero(draw, elem=st.integers(min_value=1, max_value=P-1)):
    return ElementModP(draw(elem))

@composite
def arb_elgamal_keypair(draw, elem=arb_element_mod_q_no_zero()):
    return ElGamalKeyPair(elem)
@given(arb_element_mod_q())