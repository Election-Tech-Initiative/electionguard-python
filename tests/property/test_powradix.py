from datetime import timedelta
from gmpy2 import powmod, xmpz  # pylint: disable=no-name-in-module
from hypothesis import given, settings, HealthCheck

from electionguard_tools.strategies.group import (
    elements_mod_p_no_zero,
    elements_mod_q,
)
from src.electionguard.group import ElementModP, ElementModQ, pow_p
from src.electionguard.constants import (
    PowRadixOption,
    STANDARD_CONSTANTS,
    push_new_constants,
    PrimeOption,
    pop_constants,
)
from src.electionguard.powradix import PowRadix

from tests.base_test_case import BaseTestCase


class TestPowRadix(BaseTestCase):
    """Exercise the PowRadix functionality, should be the same as regular powmod."""

    @settings(
        deadline=timedelta(milliseconds=20000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elements_mod_p_no_zero(), elements_mod_q())
    def test_powmod_integration_standard(self, p: ElementModP, q: ElementModQ):
        push_new_constants(PrimeOption.Standard, PowRadixOption.HIGH_MEMORY_USE)
        try:
            expected = pow_p(p, q)
            fp1 = p.accelerate_pow()
            self.assertEqual(expected, pow_p(fp1, q))
        except BaseException as e:
            pop_constants()
            raise e
        pop_constants()

    @settings(
        deadline=timedelta(milliseconds=20000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(elements_mod_q(), elements_mod_q())
    def test_powmod_bignums(self, q1: ElementModQ, q2: ElementModQ):
        # This test doesn't rely on the machinery to pick different election constants,
        # and forces everything into the "standard" sizes.
        g = STANDARD_CONSTANTS.generator
        q = STANDARD_CONSTANTS.small_prime
        p = STANDARD_CONSTANTS.large_prime

        q1 = xmpz(q1)
        q2 = xmpz(q2)
        new_base = powmod(xmpz(g), q1, p)
        expected = powmod(new_base, q2, p)

        pr_g = PowRadix(g, PowRadixOption.LOW_MEMORY_USE, small_prime=q, large_prime=p)
        pr_new_base = PowRadix(
            new_base, PowRadixOption.LOW_MEMORY_USE, small_prime=q, large_prime=p
        )
        actual1 = pr_new_base.pow(q2, normalize_e=False)
        actual2 = powmod(pr_g.pow(q1, normalize_e=False), q2, p)

        self.assertEqual(expected, actual1)
        self.assertEqual(expected, actual2)
