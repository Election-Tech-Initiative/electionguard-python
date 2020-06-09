from typing import NamedTuple

from .elgamal import ElGamalKeyPair
from .group import (
    ElementModQ,
    ElementModP,
    g_pow_p,
    mult_p,
    pow_p,
    a_plus_bc_q,
)
from .hash import hash_elems
from .logs import log_warning


class SchnorrProof(NamedTuple):
    """
    Representation of a Schnorr proof
    """

    k: ElementModP
    h: ElementModP
    u: ElementModQ

    def is_valid(self) -> bool:
        """
        Check validity of the `proof` for proving possession of the private key corresponding
        to `public_key`.

        :return: true if the transcript is valid, false if anything is wrong
        """

        (k, h, u) = self
        valid_public_key = k.is_valid_residue()
        in_bounds_h = h.is_in_bounds()
        in_bounds_u = u.is_in_bounds()

        c = hash_elems(k, h)
        valid_proof = g_pow_p(u) == mult_p(h, pow_p(k, c))

        success = valid_public_key and in_bounds_h and in_bounds_u and valid_proof
        if not success:
            log_warning(
                "found an invalid Schnorr proof: %s",
                str(
                    {
                        "in_bounds_h": in_bounds_h,
                        "in_bounds_u": in_bounds_u,
                        "valid_public_key": valid_public_key,
                        "valid_proof": valid_proof,
                        "proof": self,
                    }
                ),
            )
        return success


def make_schnorr_proof(keypair: ElGamalKeyPair, r: ElementModQ) -> SchnorrProof:
    """
    Given an ElGamal keypair and a nonce, generates a proof that the prover knows the secret key without revealing it.

    :param keypair: An ElGamal keypair.
    :param r: A random element in [0,Q).
    """

    k = keypair.public_key
    h = g_pow_p(r)
    c = hash_elems(k, h)
    u = a_plus_bc_q(r, keypair.secret_key, c)

    return SchnorrProof(k, h, u)
