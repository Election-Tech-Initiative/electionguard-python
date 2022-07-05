# pylint: disable=too-many-instance-attributes
from dataclasses import dataclass
from typing import List

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
    mult_q,
    int_to_q,
    ZERO_MOD_Q,
    ZERO_MOD_P,
)
from .hash import hash_elems
from .logs import log_warning
from .nonces import Nonces
from .proof import Proof, ProofUsage


@dataclass
class RangeChaumPedersenProof(Proof):
    """
    Representation of range Chaum-Pedersen proof
    """

    commitments: List[ElementModP]
    """[a0, b0, a1, b1, ..., aL, bL]"""

    challenges: List[ElementModQ]
    """[c0, c1, ..., cL, c]"""

    responses: List[ElementModQ]
    """[v0, v1, ..., vL]"""

    usage: ProofUsage = ProofUsage.RangeValue
    """A description of how to use this proof"""

    def __post_init__(self) -> None:
        super().__init__()

    def is_valid(
        self, message: ElGamalCiphertext, k: ElementModP, q: ElementModQ
    ) -> bool:
        """
        Validates a range Chaum-Pedersen proof.

        :param message: The ciphertext message
        :param k: The public encryption key
        :param q: The extended base hash of the election
        :return: Whether the proof is valid
        """
        alpha = message.pad
        beta = message.data
        commitments = self.commitments
        challenges = self.challenges
        responses = self.responses

        limit = len(responses) - 1
        assert len(commitments) == 2 * (limit + 1) and len(challenges) == limit + 2, (
            "RangeChaumPedersenProof.is_valid only supports proofs with a commitment, challenge,"
            + " and response for each possible integer value, plus one additional challenge."
        )

        # (4.A)
        valid_residue_alpha = alpha.is_valid_residue()
        valid_residue_beta = beta.is_valid_residue()
        valid_residue_pads = [
            commitments[2 * j].is_valid_residue() for j in range(limit + 1)
        ]
        valid_residue_data = [
            commitments[2 * j + 1].is_valid_residue() for j in range(limit + 1)
        ]

        # (4.B)
        c = challenges[-1]
        consistent_c_hash = c == hash_elems(q, alpha, beta, *commitments)

        # (4.C)
        in_bounds_challenges = [cj.is_in_bounds() for cj in challenges[:-1]]
        in_bounds_responses = [vj.is_in_bounds() for vj in responses]

        # (4.D)
        consistent_c_sum = c == add_q(*challenges[:-1])

        # (4.E'): check pad equations
        consistent_pads = [
            g_pow_p(vj) == mult_p(commitments[2 * j], pow_p(alpha, challenges[j]))
            for j, vj in enumerate(responses)
        ]

        # (4.F'): check data equations
        consistent_data = [
            (
                mult_p(g_pow_p(mult_q(j, challenges[j])), pow_p(k, vj))
                == mult_p(commitments[2 * j + 1], pow_p(beta, challenges[j]))
            )
            for j, vj in enumerate(responses)
        ]
        # TODO: Is saving the single unnecessary g_pow_p(0) worth adding limit + 1 many conditionals?
        # consistent_data = [
        #    (mult_p(g_pow_p(mult_q(j,cj)), pow_p(k, responses[j]))
        #        == mult_p(commitments[2*j+1], pow_p(beta, cj))) if j != 0
        #    else pow_p(k, responses[j])
        #        == mult_p(commitments[2*j+1], pow_p(beta, cj))
        #    for j,cj in enumerate(challenges[:-1])
        # ]

        success = (
            valid_residue_alpha
            and valid_residue_beta
            and all(valid_residue_pads)
            and all(valid_residue_data)
            and consistent_c_hash
            and all(in_bounds_challenges)
            and all(in_bounds_responses)
            and consistent_c_sum
            and all(consistent_pads)
            and all(consistent_data)
        )
        if not success:
            log_warning(
                "found an invalid range Chaum-Pedersen proof: "
                + str(
                    {
                        "valid_residue_alpha": valid_residue_alpha,
                        "valid_residue_beta": valid_residue_beta,
                        "valid_residue_pads": valid_residue_pads,
                        "valid_residue_data": valid_residue_data,
                        "consistent_c_hash": consistent_c_hash,
                        "in_bounds_challenges": in_bounds_challenges,
                        "in_bounds_responses": in_bounds_responses,
                        "consistent_c_sum": consistent_c_sum,
                        "consistent_pads": consistent_pads,
                        "consistent_data": consistent_data,
                        "k": k,
                        "limit": limit,
                        "proof": self,
                    }
                )
            )
        return success


@dataclass
class DisjunctiveChaumPedersenProof(Proof):
    """
    Representation of disjunctive Chaum-Pedersen proof
    """

    proof_zero_pad: ElementModP
    """a0 in the spec"""
    proof_zero_data: ElementModP
    """b0 in the spec"""
    proof_one_pad: ElementModP
    """a1 in the spec"""
    proof_one_data: ElementModP
    """b1 in the spec"""
    proof_zero_challenge: ElementModQ
    """c0 in the spec"""
    proof_one_challenge: ElementModQ
    """c1 in the spec"""
    challenge: ElementModQ
    """c in the spec"""
    proof_zero_response: ElementModQ
    """proof_zero_response in the spec"""
    proof_one_response: ElementModQ
    """proof_one_response in the spec"""
    usage: ProofUsage = ProofUsage.BinaryValue
    """a description of how to use this proof"""

    def __post_init__(self) -> None:
        super().__init__()

    def is_valid(
        self, message: ElGamalCiphertext, k: ElementModP, q: ElementModQ
    ) -> bool:
        """
        Validates a "disjunctive" Chaum-Pedersen (zero or one) proof.

        :param message: The ciphertext message
        :param k: The public key of the election
        :param q: The extended base hash of the election
        :return: Whether the proof is valid
        """

        alpha = message.pad
        beta = message.data
        a0 = self.proof_zero_pad
        b0 = self.proof_zero_data
        a1 = self.proof_one_pad
        b1 = self.proof_one_data
        c0 = self.proof_zero_challenge
        c1 = self.proof_one_challenge
        c = self.challenge
        v0 = self.proof_zero_response
        v1 = self.proof_one_response
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
        consistent_c = add_q(c0, c1) == c == hash_elems(q, alpha, beta, a0, b0, a1, b1)
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


@dataclass
class ChaumPedersenProof(Proof):
    """
    Representation of a generic Chaum-Pedersen zero-knowledge proof
    """

    pad: ElementModP
    """a in the spec"""
    data: ElementModP
    """b in the spec"""
    challenge: ElementModQ
    """c in the spec"""
    response: ElementModQ
    """v in the spec"""
    usage: ProofUsage = ProofUsage.SecretValue
    """a description of how to use this proof"""

    def __post_init__(self) -> None:
        super().__init__()

    def is_valid(
        self,
        message: ElGamalCiphertext,
        k: ElementModP,
        m: ElementModP,
        q: ElementModQ,
    ) -> bool:
        """
        Validates a Chaum-Pedersen proof (see Verification 8 in v1.1 of the specification).
        That is, verify the following:
        - The response v is in the valid range of Z_q
        - The commitments a and b are valid residues (i.e., in Z_p^r)
        - The challenge c is the hash value H(Q', A, B, a, b, M)
        - The equations g^v mod p = a*K^c mod p and A^v mod p = b*M^c mod p hold.

        :param message: The ciphertext message
        :param k: The public encryption key (K)
        :param m: The value being checked for validity (e.g., decryption share M)
        :param q: The extended base hash of the election
        :return: Whether the proof is valid
        """
        alpha = message.pad
        beta = message.data
        a = self.pad
        b = self.data
        c = self.challenge
        v = self.response
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
        # g^v mod p = a*K^c mod p
        consistent_gv = g_pow_p(v) == mult_p(a, pow_p(k, c))
        # A^v mod p = b*M^c mod p
        consistent_av = pow_p(alpha, v) == mult_p(b, pow_p(m, c))

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


@dataclass
class ConstantChaumPedersenProof(Proof):
    """
    Representation of a constant Chaum-Pedersen proof
    """

    pad: ElementModP
    """a in the spec"""
    data: ElementModP
    """b in the spec"""
    challenge: ElementModQ
    """c in the spec"""
    response: ElementModQ
    """v in the spec"""
    constant: int
    """constant value, L in the spec"""
    usage: ProofUsage = ProofUsage.ConstantValue
    """a description of how to use this proof"""

    def __post_init__(self) -> None:
        super().__init__()

    def is_valid(
        self, message: ElGamalCiphertext, k: ElementModP, q: ElementModQ
    ) -> bool:
        """
        Validates a constant Chaum-Pedersen proof (see Verification 5 in v1.1 of the specification).
        That is, verify the following:
        - The response V is in the valid range of Z_q
        - The commitments a and b are valid residues (i.e., in Z_p^r)
        - The challenge C is the hash value H(Q', α, β, a, b)
        - The equations g^v mod p = a*α^C mod p and g^(L*C)*K^V mod p = b*β^c mod p hold.
        
        :param message: The ciphertext message
        :param k: The public encryption key (K)
        :param q: The extended base hash of the election
        :return: Whether the proof is valid
        """

        alpha = message.pad
        beta = message.data
        a = self.pad
        b = self.data
        c = self.challenge
        v = self.response
        constant = self.constant
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
        same_c = c == hash_elems(q, alpha, beta, a, b)

        # g^V mod p = a*α^C mod p
        consistent_gv = g_pow_p(v) == mult_p(a, pow_p(alpha, c))
        # g^(L*C)*K^V mod p = b*β^C mod p
        consistent_kv = (mult_p(g_pow_p(mult_q(c, constant_q)), pow_p(k, v))
            == mult_p(b, pow_p(beta, c)))

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


def make_range_chaum_pedersen(
    message: ElGamalCiphertext,
    r: ElementModQ,
    k: ElementModP,
    q: ElementModQ,
    seed: ElementModQ,
    plaintext: int,
    limit: int = 1,
) -> RangeChaumPedersenProof:
    """
    Produce a proof that the message is an encryption of some integer between 0 and the limit, inclusive.
    Critically, the proof does not reveal which particular integer is encrypted.

    :param message: An ElGamal ciphertext
    :param r: The encryption nonce
    :param k: The public encryption key (K)
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    :param seed: A value for generating nonces
    :param plaintext: The integer encrypted by the ElGamal ciphertext
    :param limit: The upper limit for the range proof; default value is 1 for usual 0 or 1 encryption
    """
    assert (
        0 <= plaintext <= limit
    ), "make_range_chaum_pedersen only supports plaintexts between 0 and the limit."
    alpha = message.pad
    beta = message.data

    # Aggregate nonces
    nonces = Nonces(seed, "range-chaum-pedersen-proof")[: 2 * limit + 1]

    # Generate anticipated challenge values (for non-plaintext values)
    challenges = [
        nonces[j]
        if j < plaintext
        else nonces[j - 1]
        if j not in {plaintext, limit + 1}
        else ZERO_MOD_Q
        for j in range(limit + 2)
    ]
    # Alternatively, use slicing
    # challenges = nonces[:plaintext] + [0] + nonces[plaintext:limit] + [0]

    # Make commitments (for every value)
    commitments = [ZERO_MOD_P] * (2 * (limit + 1))
    for j in range(limit + 1):
        uj = nonces[j + limit]
        cj = challenges[j]
        commitments[2 * j] = g_pow_p(uj)
        commitments[2 * j + 1] = mult_p(
            g_pow_p(mult_q(a_minus_b_q(j, plaintext), cj)), pow_p(k, uj)
        )
        # TODO: Which is costlier: running g_pow_p(0) once or limit + 1 many checks j != limit?
        # commitments[2*j+1] = pow_p(k, uj)
        # if j != limit:
        #     commitments[2*j+1] = mult_p(g_pow_p(mult_q(a_minus_b_q(j, plaintext), cj)), commitment["data"])

    # Compute the remaining challenge values
    c = hash_elems(q, alpha, beta, *commitments)
    challenges[plaintext] = a_minus_b_q(c, add_q(*challenges))
    challenges[-1] = c

    # Calculate the response (for every value)
    responses = [
        add_q(nonces[j + limit], mult_q(challenges[j], r)) for j in range(limit + 1)
    ]

    # Present proof
    return RangeChaumPedersenProof(commitments, challenges, responses)


def make_disjunctive_chaum_pedersen(
    message: ElGamalCiphertext,
    r: ElementModQ,
    k: ElementModP,
    q: ElementModQ,
    seed: ElementModQ,
    plaintext: int,
) -> DisjunctiveChaumPedersenProof:
    """
    Produce a disjunctive proof that an encryption of a given plaintext encrypts either zero or one.
    This is just a front-end helper for `make_disjunctive_chaum_pedersen_zero` and
    `make_disjunctive_chaum_pedersen_one`.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The public encryption key (K)
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    :param seed: Used to generate other random values here
    :param plaintext: Zero or one
    """

    assert (
        0 <= plaintext <= 1
    ), "make_disjunctive_chaum_pedersen only supports plaintexts of 0 or 1"
    if plaintext == 0:
        return make_disjunctive_chaum_pedersen_zero(message, r, k, q, seed)
    return make_disjunctive_chaum_pedersen_one(message, r, k, q, seed)


def make_disjunctive_chaum_pedersen_zero(
    message: ElGamalCiphertext,
    r: ElementModQ,
    k: ElementModP,
    q: ElementModQ,
    seed: ElementModQ,
) -> DisjunctiveChaumPedersenProof:
    """
    Produces a disjunctive proof that an encryption of zero is either an encryption of zero or one.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The public encryption key (K)
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    :param seed: Used to generate other random values here
    """
    alpha = message.pad
    beta = message.data

    # Pick three random numbers in Q.
    c1, v, u0 = Nonces(seed, "disjoint-chaum-pedersen-proof")[0:3]

    # Compute the NIZKP
    a0 = g_pow_p(u0)
    b0 = pow_p(k, u0)
    a1 = g_pow_p(v)
    b1 = mult_p(pow_p(k, v), g_pow_p(c1))
    c = hash_elems(q, alpha, beta, a0, b0, a1, b1)
    c0 = a_minus_b_q(c, c1)
    v0 = a_plus_bc_q(u0, c0, r)
    v1 = a_plus_bc_q(v, c1, r)

    return DisjunctiveChaumPedersenProof(a0, b0, a1, b1, c0, c1, c, v0, v1)


def make_disjunctive_chaum_pedersen_one(
    message: ElGamalCiphertext,
    r: ElementModQ,
    k: ElementModP,
    q: ElementModQ,
    seed: ElementModQ,
) -> DisjunctiveChaumPedersenProof:
    """
    Produces a disjunctive proof that an encryption of one is either an encryption of zero or one.

    :param message: An ElGamal ciphertext
    :param r: The nonce used creating the ElGamal ciphertext
    :param k: The public encryption key (K)
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    :param seed: Used to generate other random values here
    """
    alpha = message.pad
    beta = message.data

    # Pick three random numbers in Q.
    w, v, u1 = Nonces(seed, "disjunctive-chaum-pedersen-proof")[0:3]

    # Compute the NIZKP
    a0 = g_pow_p(v)
    b0 = mult_p(pow_p(k, v), g_pow_p(w))
    a1 = g_pow_p(u1)
    b1 = pow_p(k, u1)
    c = hash_elems(q, alpha, beta, a0, b0, a1, b1)
    c0 = negate_q(w)
    c1 = add_q(c, w)
    v0 = a_plus_bc_q(v, c0, r)
    v1 = a_plus_bc_q(u1, c1, r)

    return DisjunctiveChaumPedersenProof(a0, b0, a1, b1, c0, c1, c, v0, v1)


def make_chaum_pedersen(
    message: ElGamalCiphertext,
    s: ElementModQ,
    m: ElementModP,
    seed: ElementModQ,
    q: ElementModQ,
) -> ChaumPedersenProof:
    """
    Produces a proof of knowledge to the secret key s such that
    M = A^s mod p and K = g^s mod p.
    Refer to section 3.5 in v1.1 of the specification.

    :param message: An ElGamal ciphertext
    :param s: The nonce or secret used to derive the value
    :param m: The value we are trying to prove
    :param seed: Used to generate other random values here
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    """
    alpha = message.pad
    beta = message.data

    # Pick one random number in Q.
    u = Nonces(seed, "chaum-pedersen-proof")[0]
    a = g_pow_p(u)  # g^u mod p
    b = pow_p(alpha, u)  # A^u mod p
    c = hash_elems(q, alpha, beta, a, b, m)  # H(Q', A, B, a, b, M)
    v = a_plus_bc_q(u, c, s)  # (u + c*s) mod 𝑞

    return ChaumPedersenProof(a, b, c, v)


def make_constant_chaum_pedersen(
    message: ElGamalCiphertext,
    constant: int,
    r: ElementModQ,
    k: ElementModP,
    seed: ElementModQ,
    q: ElementModQ,
) -> ConstantChaumPedersenProof:
    """
    Produces a proof that an encryption encodes a particular value.
    Refer to section 3.3.5 in v1.1 of the specification.

    :param message: An ElGamal ciphertext
    :param constant: The plaintext constant value used to make the ElGamal ciphertext (L)
    :param r: The aggregate nonce used creating the ElGamal ciphertext
    :param k: The public encryption key (K)
    :param seed: Used to generate other random values here
    :param q: A value for generating the challenge hash, usually the extended base hash (Q')
    """
    alpha = message.pad
    beta = message.data

    # Pick one random number in Z_q.
    u = Nonces(seed, "constant-chaum-pedersen-proof")[0]
    a = g_pow_p(u)  # g^u mod p
    b = pow_p(k, u)  # K^u mod p
    c = hash_elems(q, alpha, beta, a, b)  # sha256(Q', α', β', a, b)
    v = a_plus_bc_q(u, c, r) # (U + C*R) mod q

    return ConstantChaumPedersenProof(a, b, c, v, constant)