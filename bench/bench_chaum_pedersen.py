from timeit import default_timer as timer
from typing import Tuple

from numpy import average, std

from electionguard.chaum_pedersen import make_chaum_pedersen_zero, valid_chaum_pedersen
from electionguard.elgamal import elgamal_keypair_from_secret, ElGamalKeyPair, elgamal_encrypt
from electionguard.group import ElementModQ, int_to_q
from electionguard.random import RandomIterable


def chaum_pederson_bench(keypair: ElGamalKeyPair, r: ElementModQ, seed: ElementModQ) -> Tuple[float,float]:
    ciphertext = elgamal_encrypt(0, r, keypair.public_key)
    start1 = timer()
    proof = make_chaum_pedersen_zero(ciphertext, r, keypair.public_key, seed)
    end1 = timer()
    valid = valid_chaum_pedersen(proof, keypair.public_key)
    end2 = timer()
    if not valid:
        raise Exception("Wasn't expecting an invalid proof during a benchmark!")
    return (end1 - start1, end2 - end1)


if __name__ == "__main__":
    ITERS: int = 100
    r = RandomIterable(int_to_q(31337))
    seeds = r.take(ITERS)
    keypairs = list(map(lambda a: elgamal_keypair_from_secret(a), seeds))
    timing_data = list(map(lambda k: chaum_pederson_bench(k, r.next(), r.next()), keypairs))

    print("Creating Chaum-Pedersen proofs (%d iterations)" % ITERS)
    print("  Avg    = %.6f sec" % average(list(map(lambda t: t[0], timing_data))))
    print("  Stddev = %.6f sec" % std(list(map(lambda t: t[0], timing_data))))

    print("Validating Chaum-Pedersen proofs (%d iterations)" % ITERS)
    print("  Avg    = %.6f sec" % average(list(map(lambda t: t[1], timing_data))))
    print("  Stddev = %.6f sec" % std(list(map(lambda t: t[1], timing_data))))
