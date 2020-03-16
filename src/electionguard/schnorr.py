from typing import NamedTuple
from .elgamal import ElGamalKeyPair
from .group import ElementModQ, ElementModP, Q, g_pow, mult_mod_p, pow_mod_p
from .hash import hash_two_elems_mod_q


class SchnorrProof(NamedTuple):
    """
    A Schnorr proof: the prover demonstrates knowledge of the secret key of an ElGamal keypair without
    revealing the secret key.
    """
    V: ElementModP
    r: ElementModQ
    c: ElementModQ


def valid_schnorr_transcript(proof: SchnorrProof, public_key: ElementModP) -> bool:
    """
    Check validity of the `proof` for proving possession of the private key corresponding
    to `public_key`.
    :return: true if the transcript is valid
    """

    # From the RFC we need:
    #    1.  To verify A is within [1, p-1] and A^q = 1 mod p;
    #    2.  To verify V = g^r * A^c mod p.
    # We'll also double-check that the challenge field, of the proof object, was computed correctly.

    if public_key.elem == 0:
        raise Exception("public key shouldn't be zero!")

    valid_challenge = proof.c == hash_two_elems_mod_q(proof.V, public_key)
    valid_public_key = pow_mod_p(public_key, ElementModQ(Q)).elem == 1
    valid_proof = proof.V == mult_mod_p(g_pow(proof.r), pow_mod_p(public_key, proof.c))

    return valid_challenge and valid_public_key and valid_proof


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

    return SchnorrProof(V, r, c)

