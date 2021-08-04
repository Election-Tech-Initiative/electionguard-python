from datetime import timedelta
from typing import List, Dict

from hypothesis import given, HealthCheck, settings, Phase
from hypothesis.strategies import integers

from tests.base_test_case import BaseTestCase

from electionguard.ballot import CiphertextBallot
from electionguard.decrypt_with_secrets import decrypt_ballot_with_secret
from electionguard.elgamal import ElGamalCiphertext, elgamal_encrypt, elgamal_add
from electionguard.encrypt import encrypt_ballot
from electionguard.group import ElementModQ
from electionguard.manifest import Manifest
from electionguard.nonces import Nonces
from electionguardtest.election import (
    election_descriptions,
    elections_and_ballots,
    ELECTIONS_AND_BALLOTS_TUPLE_TYPE,
)
from electionguardtest.election_factory import ElectionFactory
from electionguardtest.group import elements_mod_q
from electionguardtest.tally import accumulate_plaintext_ballots


SEED = ElectionFactory.get_encryption_device().get_hash()


class TestElections(BaseTestCase):
    """Election hypothesis encryption tests"""

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(election_descriptions())
    def test_generators_yield_valid_output(self, manifest: Manifest):
        """
        Tests that our Hypothesis election strategies generate "valid" output, also exercises the full stack
        of `is_valid` methods.
        """

        self.assertTrue(manifest.is_valid())

    @settings(
        deadline=timedelta(milliseconds=10000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=5,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(
        integers(1, 3).flatmap(lambda n: elections_and_ballots(n)),
        elements_mod_q(),
    )
    def test_accumulation_encryption_decryption(
        self,
        everything: ELECTIONS_AND_BALLOTS_TUPLE_TYPE,
        nonce: ElementModQ,
    ):
        """
        Tests that decryption is the inverse of encryption over arbitrarily generated elections and ballots.

        This test uses an abitrarily generated dataset with a single public-private keypair for the election
        encryption context.  It also manually verifies that homomorphic accumulation works as expected.
        """
        # Arrange
        (
            _election_description,
            internal_manifest,
            ballots,
            secret_key,
            context,
        ) = everything

        # Tally the plaintext ballots for comparison later
        plaintext_tallies = accumulate_plaintext_ballots(ballots)
        num_ballots = len(ballots)
        num_contests = len(internal_manifest.contests)
        zero_nonce, *nonces = Nonces(nonce)[: num_ballots + 1]
        self.assertEqual(len(nonces), num_ballots)
        self.assertTrue(len(internal_manifest.contests) > 0)

        # Generate a valid encryption of zero
        encrypted_zero = elgamal_encrypt(0, zero_nonce, context.elgamal_public_key)

        # Act
        encrypted_ballots = []

        # encrypt each ballot
        for i in range(num_ballots):
            encrypted_ballot = encrypt_ballot(
                ballots[i], internal_manifest, context, SEED, nonces[i]
            )
            encrypted_ballots.append(encrypted_ballot)

            # sanity check the encryption
            self.assertIsNotNone(encrypted_ballot)
            self.assertEqual(num_contests, len(encrypted_ballot.contests))

            # decrypt the ballot with secret and verify it matches the plaintext
            decrypted_ballot = decrypt_ballot_with_secret(
                ballot=encrypted_ballot,
                internal_manifest=internal_manifest,
                crypto_extended_base_hash=context.crypto_extended_base_hash,
                public_key=context.elgamal_public_key,
                secret_key=secret_key,
                remove_placeholders=True,
            )
            self.assertEqual(ballots[i], decrypted_ballot)

        # homomorphically accumulate the encrypted ballot representations
        encrypted_tallies = _accumulate_encrypted_ballots(
            encrypted_zero, encrypted_ballots
        )

        decrypted_tallies = {}
        for object_id, encrypted_tally in encrypted_tallies.items():
            decrypted_tallies[object_id] = encrypted_tally.decrypt(secret_key)

        # loop through the contest descriptions and verify
        # the decrypted tallies match the plaintext tallies
        for contest in internal_manifest.contests:
            # Sanity check the generated data
            self.assertTrue(len(contest.ballot_selections) > 0)
            self.assertTrue(len(contest.placeholder_selections) > 0)

            decrypted_selection_tallies = [
                decrypted_tallies[selection.object_id]
                for selection in contest.ballot_selections
            ]
            decrypted_placeholder_tallies = [
                decrypted_tallies[placeholder.object_id]
                for placeholder in contest.placeholder_selections
            ]
            plaintext_tally_values = [
                plaintext_tallies[selection.object_id]
                for selection in contest.ballot_selections
            ]

            # verify the plaintext tallies match the decrypted tallies
            self.assertEqual(decrypted_selection_tallies, plaintext_tally_values)

            # validate the right number of selections including placeholders across all ballots
            self.assertEqual(
                contest.number_elected * num_ballots,
                sum(decrypted_selection_tallies) + sum(decrypted_placeholder_tallies),
            )


def _accumulate_encrypted_ballots(
    encrypted_zero: ElGamalCiphertext, ballots: List[CiphertextBallot]
) -> Dict[str, ElGamalCiphertext]:
    """
    Internal helper function for testing: takes a list of encrypted ballots as input,
    digs into all of the individual selections and then accumulates them, using
    their `object_id` fields as keys. This function only knows what to do with
    `n_of_m` elections. It's not a general-purpose tallying mechanism for other
    election types.

    Note that the output will include both "normal" and "placeholder" selections.

    :param encrypted_zero: an encrypted zero, used for the accumulation
    :param ballots: a list of encrypted ballots
    :return: a dict from selection object_id's to `ElGamalCiphertext` totals
    """
    tally: Dict[str, ElGamalCiphertext] = {}
    for ballot in ballots:
        for contest in ballot.contests:
            for selection in contest.ballot_selections:
                desc_id = (
                    selection.object_id
                )  # this should be the same as in the PlaintextBallot!
                if desc_id not in tally:
                    tally[desc_id] = encrypted_zero
                tally[desc_id] = elgamal_add(tally[desc_id], selection.ciphertext)
    return tally
