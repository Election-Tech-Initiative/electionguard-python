from typing import NamedTuple

from .elgamal import ElGamalCiphertext
from .group import (
    ElementModQ,
    ElementModP,
    g_pow_p,
    mult_p,
    pow_p,
    a_minus_b_q,
    a_plus_bc_q,
    add_q,
    negate_q,
    int_to_q,
    ZERO_MOD_Q,
)
from .hash import hash_elems
from .logs import log_warning
from .nonces import Nonces


class DisjunctiveChaumPedersenProof(NamedTuple):
    """
    Representation of disjunctive Chaum Pederson proof
    """

    a0: ElementModP
    b0: ElementModP
    a1: ElementModP
    b1: ElementModP
    c0: ElementModQ
    c1: ElementModQ
    v0: ElementModQ
    v1: ElementModQ

    def is_valid(self, message: ElGamalCiphertext, k: ElementModP) -> bool:
        """
        Validates a "disjunctive" Chaum-Pedersen (zero or one) proof.

        :param message: The ciphertext message
        :param k: The public key of the election
        :return: True if everything is consistent. False otherwise.
        """

        (alpha, beta) = message
        (a0, b0, a1, b1, c0, c1, v0, v1) = self
        in_bounds_alpha = alpha.is_valid_residue()
        in_bounds_beta = beta.is_valid_residue()
        in_bounds_a0 = a0.is_valid_residue()
        in_bounds_b0 = b0.is_valid_residue()
        in_bounds_a1 = a1.is_valid_residue()
        in_bounds_b1 = b1.is_valid_residue()
        in_bounds_c0 = c0.is_in_bounds()
        in_bounds_c1 = c1.is_in_bounds()
        in_bounds_v0 = v0.is_in_bounds()
        in_bounds_v1 = v1.is_in_bounds()
        consistent_c = add_q(c0, c1) == hash_elems(alpha, beta, a0, b0, a1, b1)
        consistent_gv0 = g_pow_p(v0) == mult_p(a0, pow_p(alpha, c0))
        consistent_gv1 = g_pow_p(v1) == mult_p(a1, pow_p(alpha, c1))
        consistent_kv0 = pow_p(k, v0) == mult_p(b0, pow_p(beta, c0))
        consistent_gc1kv1 = mult_p(g_pow_p(c1), pow_p(k, v1)) == mult_p(
            b1, pow_p(beta, c1)
        )

        success = (
            in_bounds_alpha
            and in_bounds_beta
            and in_bounds_a0
            and in_bounds_b0
            and in_bounds_a1
            and in_bounds_b1
            and in_bounds_c0
            and in_bounds_c1
            and in_bounds_v0
            and in_bounds_v1
            and consistent_c
            and consistent_gv0
            and consistent_gv1
            and consistent_kv0
            and consistent_gc1kv1
        )

        if not success:
            log_warning(
                "found an invalid Disjunctive Chaum-Pedersen proof: "
                + str(
                    {
                        "in_bounds_alpha": in_bounds_alpha,
                        "in_bounds_beta": in_bounds_beta,
                        "in_bounds_a0": in_bounds_a0,
                        "in_bounds_b0": in_bounds_b0,
                        "in_bounds_a1": in_bounds_a1,
                        "in_bounds_b1": in_bounds_b1,
                        "in_bounds_c0": in_bounds_c0,
                        "in_bounds_c1": in_bounds_c1,
                        "in_bounds_v0": in_bounds_v0,
                        "in_bounds_v1": in_bounds_v1,
                        "consistent_c": consistent_c,
                        "consistent_gv0": consistent_gv0,
                        "consistent_gv1": consistent_gv1,
                        "consistent_kv0": consistent_kv0,
                        "consistent_gc1kv1": consistent_gc1kv1,
                        "k": k,
                        "proof": self,
                    }
                ),
            )
        return success


class ChaumPedersenProof(NamedTuple):
    """
    Representation of a generic Chaum-Pedersen Zero Knowledge proof 
    """

    a: ElementModP
    b: ElementModP
    c: ElementModQ
    v: ElementModQ

    def is_valid(
        self,
        message: ElGamalCiphertext,
        k: ElementModP,
        m: ElementModP,
        q: ElementModQ,
    ) -> bool:
        """
        Validates a Chaum-Pedersen proof.
        e.g.
        - The given value 𝑣𝑖 is in the set Z𝑞
        - The given values 𝑎𝑖 and 𝑏𝑖 are both in the set Z𝑞^𝑟
        - The challenge value 𝑐 satisfies 𝑐 = 𝐻(𝑄, (𝐴, 𝐵), (𝑎 , 𝑏 ), 𝑀 ).
        - that the equations 𝑔^𝑣𝑖 = 𝑎𝑖𝐾^𝑐𝑖 mod 𝑝 and 𝐴^𝑣𝑖 = 𝑏𝑖𝑀𝑖^𝑐𝑖 mod 𝑝 are satisfied.
        
        :param message: The ciphertext message
        :param k: The public key corresponding to the private key used to encrypt 
                  (e.g. the Guardian public election key)
        :param m: The value being checked for validity
        :param q: The extended base hash of the election
        :return: True if everything is consistent. False otherwise.
        """
        (alpha, beta) = message
        (a, b, c, v) = self
        in_bounds_alpha = alpha.is_valid_residue()
        in_bounds_beta = beta.is_valid_residue()
        in_bounds_k = k.is_valid_residue()
        in_bounds_m = m.is_valid_residue()
        in_bounds_a = a.is_valid_residue()
        in_bounds_b = b.is_valid_residue()
        in_bounds_c = c.is_in_bounds()
        in_bounds_v = v.is_in_bounds()
        in_bounds_q = q.is_in_bounds()

        same_c = c == hash_elems(q, alpha, beta, a, b, m)
        consistent_gv = (
            in_bounds_v
            and in_bounds_a
            and in_bounds_c
            and in_bounds_v
            # The equation 𝑔^𝑣𝑖 = 𝑎𝑖𝐾^𝑐𝑖
            and g_pow_p(v) == mult_p(a, pow_p(k, c))
        )

        # The equation 𝐴^𝑣𝑖 = 𝑏𝑖𝑀𝑖^𝑐𝑖 mod 𝑝
        consistent_av = (
            in_bounds_alpha
            and in_bounds_b
            and in_bounds_c
            and in_bounds_v
            and pow_p(alpha, v) == mult_p(b, pow_p(m, c))
        )

        success = (
            in_bounds_alpha
            and in_bounds_beta
            and in_bounds_k
            and in_bounds_m
            and in_bounds_a
            and in_bounds_b
            and in_bounds_c
            and in_bounds_v
            and in_bounds_q
            and same_c
            and consistent_gv
            and consistent_av
        )

        if not success:
            log_warning(
                "found an invalid Chaum-Pedersen proof: "
                + str(
                    {
                        "in_bounds_alpha": in_bounds_alpha,
                        "in_bounds_beta": in_bounds_beta,
                        "in_bounds_k": in_bounds_k,
                        "in_bounds_m": in_bounds_m,
                        "in_bounds_a": in_bounds_a,
                        "in_bounds_b": in_bounds_b,
                        "in_bounds_c": in_bounds_c,
                        "in_bounds_v": in_bounds_v,
                        "in_bounds_q": in_bounds_q,
                        "same_c": same_c,
                        "consistent_gv": consistent_gv,
                        "consistent_av": consistent_av,
                        "k": k,
                        "q": q,
                        "proof": self,
                    }
                ),
            )
        return success


class ConstantChaumPedersenProof(NamedTuple):
    """
    Representation of constant Chaum Pederson proof
    """

    a: ElementModP
    b: ElementModP
    c: ElementModQ
    v: ElementModQ
    constant: int

    def is_valid(self, message: ElGamalCiphertext, k: ElementModP) -> bool:
        """
        Validates a "constant" Chaum-Pedersen proof.
        e.g. that the equations 𝑔𝑉 = 𝑎𝐴𝐶 mod 𝑝 and 𝑔𝐿𝐾𝑣 = 𝑏𝐵𝐶 mod 𝑝 are satisfied.

        :param message: The ciphertext message
        :param K: The public key of the election
        :return: True if everything is consistent. False otherwise.
        """

        (alpha, beta) = message
        (a, b, c, v, constant) = self
        in_bounds_alpha = alpha.is_valid_residue()
        in_bounds_beta = beta.is_valid_residue()
        in_bounds_a = a.is_valid_residue()
        in_bounds_b = b.is_valid_residue()
        in_bounds_c = c.is_in_bounds()
        in_bounds_v = v.is_in_bounds()
        tmp = int_to_q(constant)
        if tmp is None:
            constant_q = ZERO_MOD_Q
            in_bounds_constant = False
        else:
            constant_q = tmp
            in_bounds_constant = True

        # this is an arbitrary constant check to verify that decryption will be performant
        # in some use cases this value may need to be increased
        sane_constant = 0 <= constant < 1_000_000_000
        same_c = c == hash_elems(alpha, beta, a, b)
        consistent_gv = (
            in_bounds_v
            and in_bounds_a
            and in_bounds_alpha
            and in_bounds_c
            # The equation 𝑔^𝑉 = 𝑎𝐴^𝐶 mod 𝑝
            and g_pow_p(v) == mult_p(a, pow_p(alpha, c))
        )

        # The equation 𝑔^𝐿𝐾^𝑣 = 𝑏𝐵^𝐶 mod 𝑝
        consistent_kv = in_bounds_constant and mult_p(
            g_pow_p(mult_p(c, constant_q)), pow_p(k, v)
        ) == mult_p(b, pow_p(beta, c))

        success = (
            in_bounds_alpha
            and in_bounds_beta
            and in_bounds_a
            and in_bounds_b
            and in_bounds_c
            and in_bounds_v
            and same_c
            and in_bounds_constant
            and sane_constant
            and consistent_gv
            and consistent_kv
        )

        if not success:
            log_warning(
                "found an invalid Constant Chaum-Pedersen proof: "
                + str(
                    {
                        "in_bounds_alpha": in_bounds_alpha,
                        "in_bounds_beta": in_bounds_beta,
                        "in_bounds_a": in_bounds_a,
                        "in_bounds_b": in_bounds_b,
                        "in_bounds_c": in_bounds_c,
                        "in_bounds_v": in_bounds_v,
                        "in_bounds_constant": in_bounds_constant,
                        "sane_constant": sane_constant,
                        "same_c": same_c,
                        "consistent_gv": consistent_gv,
                        "consistent_kv": consistent_kv,
                        "k": k,
                        "proof": self,
                    }
                ),
            )
        return success


def make_disjunctive_chaum_pedersen(
    message: ElGamalCiphertext,
    r: ElementModQ,
    k: ElementModP,
    seed: ElementModQ,
    plaintext: int,
) -> DisjunctiveChaumPedersenProof:
    """
    Produce a "disjunctive" proof that an encryption of a given plaintext is either an encrypted zero or one.
    This is just a front-end helper for `make_disjunctive_chaum_pedersen_zero` and
    `make_disjunctive_chaum_pedersen_one`.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The ElGamal public key for the election
    :param seed: Used to generate other random values here
    :param plaintext: Zero or one
    """

    assert (
        0 <= plaintext <= 1
    ), "make_disjunctive_chaum_pedersen only supports plaintexts of 0 or 1"
    if plaintext == 0:
        return make_disjunctive_chaum_pedersen_zero(message, r, k, seed)
    else:
        return make_disjunctive_chaum_pedersen_one(message, r, k, seed)


def make_disjunctive_chaum_pedersen_zero(
    message: ElGamalCiphertext, r: ElementModQ, k: ElementModP, seed: ElementModQ
) -> DisjunctiveChaumPedersenProof:
    """
    Produces a "disjunctive" proof that an encryption of zero is either an encrypted zero or one.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The ElGamal public key for the election
    :param seed: Used to generate other random values here
    """
    (alpha, beta) = message

    # Pick three random numbers in Q.
    c1, v1, u0 = Nonces(seed, "disjoint-chaum-pedersen-proof")[0:3]

    # Compute the NIZKP
    a0 = g_pow_p(u0)
    b0 = pow_p(k, u0)
    q_minus_c1 = negate_q(c1)
    a1 = mult_p(g_pow_p(v1), pow_p(alpha, q_minus_c1))
    b1 = mult_p(pow_p(k, v1), g_pow_p(c1), pow_p(beta, q_minus_c1))
    c = hash_elems(alpha, beta, a0, b0, a1, b1)
    c0 = a_minus_b_q(c, c1)
    v0 = a_plus_bc_q(u0, c0, r)

    return DisjunctiveChaumPedersenProof(a0, b0, a1, b1, c0, c1, v0, v1)


def make_disjunctive_chaum_pedersen_one(
    message: ElGamalCiphertext, r: ElementModQ, k: ElementModP, seed: ElementModQ
) -> DisjunctiveChaumPedersenProof:
    """
    Produces a "disjunctive" proof that an encryption of one is either an encrypted zero or one.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The ElGamal public key for the election
    :param seed: Used to generate other random values here
    """
    (alpha, beta) = message

    # Pick three random numbers in Q.
    c0, v0, u1 = Nonces(seed, "disjoint-chaum-pedersen-proof")[0:3]

    # Compute the NIZKP
    q_minus_c0 = negate_q(c0)
    a0 = mult_p(g_pow_p(v0), pow_p(alpha, q_minus_c0))
    b0 = mult_p(pow_p(k, v0), pow_p(beta, q_minus_c0))
    a1 = g_pow_p(u1)
    b1 = pow_p(k, u1)
    c = hash_elems(alpha, beta, a0, b0, a1, b1)
    c1 = a_minus_b_q(c, c0)
    v1 = a_plus_bc_q(u1, c1, r)

    return DisjunctiveChaumPedersenProof(a0, b0, a1, b1, c0, c1, v0, v1)


def make_chaum_pedersen(
    message: ElGamalCiphertext,
    s: ElementModQ,
    m: ElementModP,
    seed: ElementModQ,
    hash_header: ElementModQ,
) -> ChaumPedersenProof:
    """
    Produces a proof that a given value corresponds to a specific encryption.
    computes: 𝑀 =𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝

    :param message: An ElGamal ciphertext
    :param s: The nonce or secret used to derive the value
    :param m: The value we are trying to prove
    :param seed: Used to generate other random values here
    :param hash_header: A value used when generating the challenge, 
                        usually the election extended base hash (𝑄')
    """
    (alpha, beta) = message

    # Pick one random number in Q.
    u = Nonces(seed, "constant-chaum-pedersen-proof")[0]
    a = g_pow_p(u)  # 𝑔^𝑢𝑖 mod 𝑝
    b = pow_p(alpha, u)  # 𝐴^𝑢𝑖 mod 𝑝
    c = hash_elems(hash_header, alpha, beta, a, b, m)  # sha256(𝑄', A, B, a𝑖, b𝑖, 𝑀𝑖)
    v = a_plus_bc_q(u, c, s)  # (𝑢𝑖 + 𝑐𝑖𝑠𝑖) mod 𝑞

    return ChaumPedersenProof(a, b, c, v)


def make_constant_chaum_pedersen(
    message: ElGamalCiphertext,
    constant: int,
    r: ElementModQ,
    k: ElementModP,
    seed: ElementModQ,
) -> ConstantChaumPedersenProof:
    """
    Produces a proof that a given encryption corresponds to a specific total value.

    :param message: An ElGamal ciphertext
    :param constant: The plaintext constant value used to make the ElGamal ciphertext (L in the spec)
    :param r: The aggregate nonce used creating the ElGamal ciphertext
    :param k: The ElGamal public key for the election
    :param seed: Used to generate other random values here
    """
    (alpha, beta) = message

    # Pick one random number in Q.
    u = Nonces(seed, "constant-chaum-pedersen-proof")[0]
    a = g_pow_p(u)  # 𝑔^𝑢𝑖 mod 𝑝
    b = pow_p(k, u)  # 𝐴^𝑢𝑖 mod 𝑝
    c = hash_elems(alpha, beta, a, b)  # sha256(𝑄', A, B, a, b)
    v = a_plus_bc_q(u, c, r)

    return ConstantChaumPedersenProof(a, b, c, v, constant)
