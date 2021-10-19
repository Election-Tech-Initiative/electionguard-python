from dataclasses import dataclass
from statistics import mean, stdev
from timeit import default_timer as timer
from typing import Dict, Tuple

from electionguard.chaum_pedersen import make_disjunctive_chaum_pedersen_zero
from electionguard.constants import (
    PowRadixOption,
    push_new_constants,
    PrimeOption,
    pop_constants,
)
from electionguard.elgamal import elgamal_encrypt, elgamal_keypair_random
from electionguard.group import ElementModQ, ONE_MOD_Q, ElementModP
from electionguard.nonces import Nonces
from electionguard.utils import get_optional


@dataclass
class BenchInput:
    """Input for benchmark"""

    public_key: ElementModP
    r: ElementModQ
    s: ElementModQ


def chaum_pedersen_bench(bi: BenchInput) -> Tuple[float, float]:
    """
    Given an input (instance of the BenchInput tuple), constructs and validates
    a disjunctive Chaum-Pedersen proof, returning the time (in seconds) to do each operation.
    """
    ciphertext = get_optional(elgamal_encrypt(0, bi.r, bi.public_key))
    start1 = timer()
    proof = make_disjunctive_chaum_pedersen_zero(
        ciphertext, bi.r, bi.public_key, ONE_MOD_Q, bi.s
    )
    end1 = timer()
    valid = proof.is_valid(ciphertext, bi.public_key, ONE_MOD_Q)
    end2 = timer()
    if not valid:
        raise Exception("Wasn't expecting an invalid proof during a benchmark!")
    return end1 - start1, end2 - end1


if __name__ == "__main__":
    push_new_constants(PrimeOption.Standard)  # make sure we're not using test constants

    speedup: Dict[int, float] = {}
    size = 500
    r_values = list(Nonces(ElementModQ(31337))[0:size])
    s_values = list(Nonces(ElementModQ(31338))[0:size])
    keypair = elgamal_keypair_random()

    proof_speed = {}
    verify_speed = {}

    for powRadixOption in PowRadixOption:
        print(f"Benchmark: {str(powRadixOption)}, problem size: {size}")
        precompute_start = timer()
        push_new_constants(pow_radix_option=powRadixOption)
        faster_keypair = keypair.accelerate_pow()
        precompute_end = timer()
        print(f"  Precompute time: {precompute_end - precompute_start:.3f} sec")

        inputs = [
            BenchInput(faster_keypair.public_key, r_values[i], s_values[i])
            for i in range(0, size)
        ]
        start_time = timer()
        timing_data = [chaum_pedersen_bench(bi) for bi in inputs]
        end_time = timer()

        avg_proof = mean([t[0] for t in timing_data])
        std_proof = stdev([t[0] for t in timing_data])
        proof_speed[powRadixOption] = avg_proof

        avg_verify = mean([t[1] for t in timing_data])
        std_verify = stdev([t[1] for t in timing_data])
        verify_speed[powRadixOption] = avg_verify

        print(
            f"  Creating Chaum-Pedersen proofs:   {avg_proof*1000:7.3f} +/- {std_proof*1000:.3f} ms / proof"
        )
        print(
            f"  Validating Chaum-Pedersen proofs: {avg_verify*1000:7.3f} +/- {std_verify*1000:.3f} ms / proof"
        )
        pop_constants()

    for powRadixOption in PowRadixOption:
        if powRadixOption != PowRadixOption.NO_ACCELERATION:
            proof_ratio = (
                proof_speed[PowRadixOption.NO_ACCELERATION]
                / proof_speed[powRadixOption]
            )
            verify_ratio = (
                verify_speed[PowRadixOption.NO_ACCELERATION]
                / verify_speed[powRadixOption]
            )
            print(
                f"Speedup of {powRadixOption:32} for proofs      : {proof_ratio: .3f}"
            )
            print(
                f"Speedup of {powRadixOption:32} for verification: {verify_ratio: .3f}"
            )
