from typing import NamedTuple

from .elgamal import ElGamalKeyPair
from .group import ElementModQ, ElementModP, Q, g_pow, mult_mod_p, pow_mod_p, validate_p, validate_q, \
    validate_p_no_zero
from .hash import hash_two_elems_mod_q


class SchnorrProof(NamedTuple):
    """
    A Schnorr proof: the prover demonstrates knowledge of the secret key of an ElGamal keypair without
    revealing the secret key.
    """
    public_key: ElementModP
    V: ElementModP
    r: ElementModQ


def valid_schnorr_transcript(proof: SchnorrProof) -> bool:
    """
    Check validity of the `proof` for proving possession of the private key corresponding
    to `public_key`.
    :return: true if the transcript is valid
    """

    # From the RFC we need:
    #    1.  To verify A is within [1, p-1] and A^q = 1 mod p;
    #    2.  To verify V = g^r * A^c mod p.

    validate_p_no_zero(proof.public_key)
    validate_p(proof.V)
    validate_q(proof.r)

    c = hash_two_elems_mod_q(proof.V, proof.public_key)
    valid_public_key = pow_mod_p(proof.public_key, ElementModQ(Q)).elem == 1
    valid_proof = proof.V == mult_mod_p(g_pow(proof.r), pow_mod_p(proof.public_key, c))

    return valid_public_key and valid_proof


def make_schnorr_proof(keypair: ElGamalKeyPair, nonce: ElementModQ) -> SchnorrProof:
    """
    Given an ElGamal keypair and a nonce, generates a proof that the prover knows the secret key without revealing it.
    :param keypair: An ElGamal keypair.
    :param nonce: A random element in [0,Q).
    """

    # https://tools.ietf.org/html/rfc8235
    #    ... to prove the knowledge of the exponent for A = g^a, Alice
    #    generates a Schnorr NIZK proof that contains: {UserID, OtherInfo, V =
    #    g^v mod p, r = v - a*c mod q}, where c = H(g || V || A || UserID ||
    #    OtherInfo).
    V = g_pow(nonce)
    c = hash_two_elems_mod_q(V, keypair.public_key)
    r = ElementModQ((nonce.elem - keypair.secret_key.elem * c.elem) % Q)

    return SchnorrProof(keypair.public_key, V, r)
