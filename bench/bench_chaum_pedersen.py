from multiprocessing import Pool, cpu_count
from timeit import default_timer as timer
from typing import Tuple, NamedTuple

from numpy import average, std

from electionguard.chaum_pedersen import make_chaum_pedersen_zero, valid_chaum_pedersen
from electionguard.elgamal import elgamal_keypair_from_secret, ElGamalKeyPair, elgamal_encrypt
from electionguard.group import ElementModQ, int_to_q
from electionguard.random import RandomIterable


class BenchInput(NamedTuple):
    keypair: ElGamalKeyPair
    rands: ElementModQ
    seed: ElementModQ


def chaum_pederson_bench(i: BenchInput) -> Tuple[float, float]:
    (keypair, r, seed) = i
    ciphertext = elgamal_encrypt(0, r, keypair.public_key)
    start1 = timer()
    proof = make_chaum_pedersen_zero(ciphertext, r, keypair.public_key, seed)
    end1 = timer()
    valid = valid_chaum_pedersen(proof, keypair.public_key)
    end2 = timer()
    if not valid:
        raise Exception("Wasn't expecting an invalid proof during a benchmark!")
    return end1 - start1, end2 - end1


if __name__ == "__main__":
    ITERS: int = 100
    rands = RandomIterable(int_to_q(31337))
    seeds = rands.take(ITERS)
    inputs = list(map(lambda a: BenchInput(elgamal_keypair_from_secret(a), rands.next(), rands.next()), seeds))
    start_all_scalar = timer()
    timing_data = list(map(lambda i: chaum_pederson_bench(i), inputs))
    end_all_scalar = timer()

    print("Creating Chaum-Pedersen proofs (%d iterations)" % ITERS)
    avg_proof_scalar = average(list(map(lambda t: t[0], timing_data)))
    std_proof_scalar = std(list(map(lambda t: t[0], timing_data)))
    print("  Avg    = %.6f sec" % avg_proof_scalar)
    print("  Stddev = %.6f sec" % std_proof_scalar)

    print("Validating Chaum-Pedersen proofs (%d iterations)" % ITERS)
    avg_verify_scalar = average(list(map(lambda t: t[1], timing_data)))
    std_verify_scalar = std(list(map(lambda t: t[1], timing_data)))
    print("  Avg    = %.6f sec" % avg_verify_scalar)
    print("  Stddev = %.6f sec" % std_verify_scalar)

    # Now, with parallelism!
    print("Checking parallel speedup, detected %d CPUs" % cpu_count())
    pool = Pool(cpu_count())
    start_all_parallel = timer()
    timing_data_parallel = pool.map(chaum_pederson_bench, inputs)
    end_all_parallel = timer()

    print("Parallel speedup: %.3fx" % ((end_all_scalar - start_all_scalar) / (end_all_parallel - start_all_parallel)))
