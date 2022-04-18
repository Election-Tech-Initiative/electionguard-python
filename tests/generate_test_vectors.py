import os
from datetime import timedelta
from hypothesis import given, HealthCheck, settings, Phase

from tests.base_test_case import BaseTestCase

from electionguard_tools.strategies.election import (
    election_descriptions,
    elections_and_ballots,
)
from electionguard.elgamal import ElGamalKeyPair
from electionguard.encrypt import encrypt_ballot
import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard.manifest import InternalManifest
from electionguard.manifest import Manifest
from electionguard.group import (
    ElementModQ,
    TWO_MOD_P,
    g_pow_p,
)
from electionguard.serialize import to_file

SEED = ElementModQ(8813)
NONCE_SEED = ElementModQ(40358)
OUTPUT_DIRECTORY = "./test_vectors"  # relative to the cwd


class TestElections(BaseTestCase):
    """Election hypothesis encryption tests"""

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=5,
    )
    @given(election_descriptions())
    def test_vector_generate(self, manifest: Manifest):
        ballot_factory = BallotFactory.BallotFactory()
        election_factory = ElectionFactory.ElectionFactory()

        keypair = ElGamalKeyPair(TWO_MOD_P, g_pow_p(TWO_MOD_P))
        election = manifest
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            election, keypair.public_key
        )

        ballots = ballot_factory.generate_fake_plaintext_ballots_for_election(
            internal_manifest, 5
        )

        test_vectors = []
        for ballot in ballots:
            test = {
                "manifest": manifest,
                "ballot": ballot,
            }

            result_from_seed = encrypt_ballot(
                ballot, internal_manifest, context, SEED, NONCE_SEED
            )
            test["output"] = str(result_from_seed.crypto_hash)
            test_vectors.append(test)

        test_cases = {
            "seed": SEED.data,
            "nonce_seed": NONCE_SEED.data,
            "vectors": test_vectors,
        }

        to_file(
            test_cases,
            f"testcases-{test_vectors[0]['output'][:4]}",
            os.path.join(os.getcwd(), OUTPUT_DIRECTORY),
        )
