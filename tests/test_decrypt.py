import unittest
from datetime import timedelta
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers

from electionguard.encrypt import (
    contest_from,
    encrypt_ballot,
    encrypt_contest,
    encrypt_selection,
    selection_from,
    EncryptionCompositor
)

from electionguard.decrypt import (
    decrypt_selection_with_secret,
    decrypt_selection_with_nonce
)

from electionguard.election import (
    CyphertextElection,
    ContestDescription,
    SelectionDescription,
    VoteVariationType
)

from electionguard.elgamal import (
    ElGamalKeyPair,
    elgamal_keypair_from_secret,
    elgamal_add,
)

from electionguard.group import (
    ElementModQ,
    TWO_MOD_Q,
    int_to_q,
    add_q,
    Q,
    TWO_MOD_P,
    mult_p,
)

from electionguardtest.elgamal import arb_elgamal_keypair
from electionguardtest.group import arb_element_mod_q_no_zero

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()

class TestDecrypt(unittest.TestCase):

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
    )
    @given(
        ElectionFactory.get_selection_description_well_formed(),
        arb_elgamal_keypair(),
        arb_element_mod_q_no_zero(),
    )
    def test_encrypt_selection_valid_input_succeeds(self,
        selection_description: Tuple[str, SelectionDescription], 
        keypair: ElGamalKeyPair,
        seed: ElementModQ):

        # Arrange
        _, description = selection_description
        data = ballot_factory.get_random_selection_from(description)

        # Act
        subject = encrypt_selection(data, description, keypair.public_key, seed)
        result_from_key = decrypt_selection_with_secret(subject, description, keypair.public_key, keypair.secret_key)
        result_from_nonce = decrypt_selection_with_nonce(subject, description, keypair.public_key, subject.nonce)

        # Assert
        self.assertIsNotNone(result_from_key)
        self.assertIsNotNone(result_from_nonce)
        self.assertEqual(data.plaintext, result_from_key.plaintext)
        self.assertEqual(data.plaintext, result_from_nonce.plaintext)