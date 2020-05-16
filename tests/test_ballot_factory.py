import unittest
from copy import deepcopy
from datetime import timedelta
from random import Random
from typing import Tuple

from hypothesis import HealthCheck
from hypothesis import given, settings
from hypothesis.strategies import integers

from electionguard.ballot import PlaintextBallotContest
from electionguard.encrypt import (
    encrypt_contest,
    encrypt_selection,
    EncryptionCompositor,
)

from electionguard.decrypt import (
    decrypt_selection_with_secret,
    decrypt_selection_with_nonce,
    decrypt_contest_with_secret,
    decrypt_contest_with_nonce,
    decrypt_ballot_with_nonce,
    decrypt_ballot_with_secret,
)

from electionguard.election import (
    ContestDescription,
    SelectionDescription,
    generate_placeholder_selections_from,
    contest_description_with_placeholders_from,
    ContestDescriptionWithPlaceholders,
    VoteVariationType,
)

from electionguard.elgamal import ElGamalKeyPair, elgamal_keypair_from_secret

from electionguard.group import (
    ElementModQ,
    TWO_MOD_P,
    mult_p,
    TWO_MOD_Q,
    ONE_MOD_Q,
)

from electionguardtest.elgamal import arb_elgamal_keypair
from electionguardtest.group import arb_element_mod_q_no_zero

import electionguardtest.ballot_factory as BallotFactory
import electionguardtest.election_factory as ElectionFactory

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestBallotFactory(unittest.TestCase):
    def test_contest_simple1(self):
        # this tries to simplify and reproduce a failure that occurred in
        # test_decrypt_contest_valid_input_succeeds

        description = ContestDescriptionWithPlaceholders(
            object_id="0@A.com-contest",
            electoral_district_id="0@A.com-gp-unit",
            sequence_order=1,
            vote_variation=VoteVariationType.n_of_m,
            number_elected=1,
            votes_allowed=1,
            name="",
            ballot_selections=[
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=0,
                ),
                SelectionDescription(
                    object_id="0@A.com-selection",
                    candidate_id="0@A.com",
                    sequence_order=1,
                ),
            ],
            ballot_title=None,
            ballot_subtitle=None,
            placeholder_selections=[
                SelectionDescription(
                    object_id="0@A.com-contest-2-placeholder",
                    candidate_id="0@A.com-contest-2-candidate",
                    sequence_order=2,
                )
            ],
        )

        data: PlaintextBallotContest = ballot_factory.get_random_contest_from(
            description, Random(0)
        )

        self.assertTrue(
            data.is_valid(description.object_id, description.number_elected,)
        )

        placeholders = generate_placeholder_selections_from(description)
        description_with_placeholders = contest_description_with_placeholders_from(
            description, placeholders
        )
