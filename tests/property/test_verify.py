# pylint: disable=protected-access
from datetime import timedelta
from typing import Dict
from hypothesis import HealthCheck, Phase
from hypothesis import given, settings
from tests.base_test_case import BaseTestCase

from electionguard.data_store import DataStore
from electionguard.decryption import compute_decryption_share
from electionguard.decryption_share import DecryptionShare
from electionguard.decrypt_with_shares import decrypt_tally
from electionguard.election_builder import ElectionBuilder
from electionguard.elgamal import ElGamalKeyPair
from electionguard.encrypt import EncryptionMediator
from electionguard.key_ceremony import CeremonyDetails
from electionguard.key_ceremony_mediator import KeyCeremonyMediator
from electionguard.tally import tally_ballots
from electionguard.type import GuardianId
from electionguard.utils import get_optional

from electionguard_verify.verify import (
    verify_ballot,
    verify_decryption,
)

import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard_tools.strategies.elgamal import elgamal_keypairs
from electionguard_tools.helpers.key_ceremony_orchestrator import (
    KeyCeremonyOrchestrator,
)

election_factory = ElectionFactory.ElectionFactory()
ballot_factory = BallotFactory.BallotFactory()


class TestVerify(BaseTestCase):
    """Test ballot verification"""

    @settings(
        deadline=timedelta(milliseconds=2000),
        suppress_health_check=[HealthCheck.too_slow],
        max_examples=10,
        # disabling the "shrink" phase, because it runs very slowly
        phases=[Phase.explicit, Phase.reuse, Phase.generate, Phase.target],
    )
    @given(elgamal_keypairs())
    def test_verify_ballot(self, keypair: ElGamalKeyPair):
        # Arrange
        manifest = election_factory.get_simple_manifest_from_file()
        internal_manifest, context = election_factory.get_fake_ciphertext_election(
            manifest, keypair.public_key
        )

        data = ballot_factory.get_simple_ballot_from_file()
        device = election_factory.get_encryption_device()
        operator = EncryptionMediator(internal_manifest, context, device)

        encrypted_ballot = operator.encrypt(data)
        self.assertIsNotNone(encrypted_ballot)

        # Act
        verification = verify_ballot(encrypted_ballot, manifest, context)

        # Assert
        self.assertIsNotNone(verification)
        self.assertTrue(verification.verified)

    def test_verify_decryption(self):
        # Arrange
        NUMBER_OF_GUARDIANS = 3
        QUORUM = 2
        CEREMONY_DETAILS = CeremonyDetails(NUMBER_OF_GUARDIANS, QUORUM)

        key_ceremony_mediator = KeyCeremonyMediator(
            "key_ceremony_mediator_mediator", CEREMONY_DETAILS
        )
        guardians = KeyCeremonyOrchestrator.create_guardians(CEREMONY_DETAILS)
        KeyCeremonyOrchestrator.perform_full_ceremony(guardians, key_ceremony_mediator)
        joint_public_key = key_ceremony_mediator.publish_joint_key()
        election_public_keys = key_ceremony_mediator._election_public_keys

        # Setup the election
        manifest = election_factory.get_fake_manifest()
        builder = ElectionBuilder(NUMBER_OF_GUARDIANS, QUORUM, manifest)
        builder.set_public_key(joint_public_key.joint_public_key)
        builder.set_commitment_hash(joint_public_key.commitment_hash)
        internal_manifest, context = get_optional(builder.build())

        # generate encrypted tally
        ballot_store = DataStore()
        ciphertext_tally = tally_ballots(ballot_store, internal_manifest, context)

        # precompute decryption shares for specific selection for the guardians
        shares: Dict[GuardianId, DecryptionShare] = {
            guardian.id: compute_decryption_share(
                guardian._election_keys,
                ciphertext_tally,
                context,
            )
            for guardian in guardians
        }

        plaintext_tally = decrypt_tally(
            ciphertext_tally, shares, context.crypto_extended_base_hash
        )

        # Act
        verification = verify_decryption(plaintext_tally, election_public_keys, context)

        # Assert
        self.assertIsNotNone(verification)
        self.assertTrue(verification.verified)
