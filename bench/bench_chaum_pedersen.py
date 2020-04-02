from multiprocessing import Pool, cpu_count
from timeit import default_timer as timer
from typing import Tuple, NamedTuple, Dict

from numpy import average, std

from electionguard.chaum_pedersen import (
    make_disjunctive_chaum_pedersen_zero,
    is_valid_disjunctive_chaum_pedersen,
)
from electionguard.elgamal import (
    elgamal_keypair_from_secret,
    ElGamalKeyPair,
    elgamal_encrypt,
)
from electionguard.group import ElementModQ, int_to_q
from electionguard.nonces import Nonces


# Why are we passing this tuple around rather than just passing three arguments?
# Makes it easier to run Pool.map().
class BenchInput(NamedTuple):
    keypair: ElGamalKeyPair
    r: ElementModQ
    s: ElementModQ


def chaum_pedersen_bench(bi: BenchInput) -> Tuple[float, float]:
    """
    Given an input (instance of the BenchInput tuple), constructs and validates
    a disjunctive Chaum-Pedersen proof, returning the time (in seconds) to do each operation.
    """
    (keypair, r, s) = bi
    ciphertext = elgamal_encrypt(0, r, keypair.public_key)
    start1 = timer()
    proof = make_disjunctive_chaum_pedersen_zero(ciphertext, r, keypair.public_key, s)
    end1 = timer()
    valid = is_valid_disjunctive_chaum_pedersen(ciphertext, proof, keypair.public_key)
    end2 = timer()
    if not valid:
        raise Exception("Wasn't expecting an invalid proof during a benchmark!")
    return end1 - start1, end2 - end1


def identity(x: int) -> int:
    """Cheesy function used just to warm up the parallel mapper prior to benchmarking."""
    return x


if __name__ == "__main__":
    problem_sizes = (100, 500, 1000, 5000)
    rands = Nonces(int_to_q(31337))
    speedup: Dict[int, float] = {}
    print(f"CPUs detected: {cpu_count()}, launching thread pool")
    pool = Pool(cpu_count())
    results = pool.map(identity, range(1, 30000))  # warm up
    assert results == list(range(1, 30000))

    bench_start = timer()

    for size in problem_sizes:
        print("Benchmarking on problem size: ", size)
        seeds = rands[0:size]
        inputs = list(
            map(
                lambda a: BenchInput(
                    elgamal_keypair_from_secret(a), rands[size], rands[size + 1]
                ),
                seeds,
            )
        )
        start_all_scalar = timer()
        timing_data = list(map(lambda i: chaum_pedersen_bench(i), inputs))
        end_all_scalar = timer()

        print(f"  Creating Chaum-Pedersen proofs ({size} iterations)")
        avg_proof_scalar = average(list(map(lambda t: t[0], timing_data)))
        std_proof_scalar = std(list(map(lambda t: t[0], timing_data)))
        print(f"    Avg    = {avg_proof_scalar:.6f} sec")
        print(f"    Stddev = {std_proof_scalar:.6f} sec")

        print(f"  Validating Chaum-Pedersen proofs ({size} iterations)")
        avg_verify_scalar = average(list(map(lambda t: t[1], timing_data)))
        std_verify_scalar = std(list(map(lambda t: t[1], timing_data)))
        print(f"    Avg    = {avg_verify_scalar:.6f} sec")
        print(f"    Stddev = {std_verify_scalar:.6f} sec")

        # Now, with parallelism!
        start_all_parallel = timer()
        timing_data_parallel = pool.map(chaum_pedersen_bench, inputs)
        end_all_parallel = timer()

        speedup[size] = (end_all_scalar - start_all_scalar) / (
            end_all_parallel - start_all_parallel
        )
        print(f"  Parallel speedup: {speedup[size]:.3f}x")

    print()
    print("PARALLELISM SPEEDUPS")
    print("Size / Speedup")
    for size in problem_sizes:
        print(f"{size:4d} / {speedup[size]:.3f}x")
    pool.close()  # apparently necessary to avoid warnings from the Pool system

    bench_end = timer()
    print()
    print(f"Total benchmark runtime: {bench_end - bench_start} sec")

##############################################################################################################
# Performance conclusions (Dan Wallach, 21 March 2020):

# On my MacPro (Xeon 6-core with hyperthreading, 3.5GHz, Python 3.8), this benchmark runs in roughly 5 minutes
# and reports that C-P proofs take 10-11ms to compute and 23-24ms to verify. The parallelism numbers are:

# Size / Speedup
#  100 / 5.749x
#  500 / 5.765x
# 1000 / 5.507x
# 5000 / 5.548x

# I've never seen this break 6x, and tweaking various parameters (e.g., cpu_count() returns 12, so I've
# tried 6) yielded no significant improvement.  One thing that seems to matter a lot: creating a Pool is
# a heavyweight operation. Keeping it around and reusing it has a significant impact on performance.

# Moral of the story: the Pool.map() method is very much "good enough" to squeeze useful parallelism out
# of any machine where we'll be verifying a lot of ballots. If we need radically more throughput, we're
# probably going to need to move to running on clusters.
