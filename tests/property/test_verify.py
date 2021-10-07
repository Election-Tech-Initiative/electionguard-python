from datetime import timedelta
from hypothesis import HealthCheck, Phase
from hypothesis import given, settings
from tests.base_test_case import BaseTestCase

from electionguard.elgamal import ElGamalKeyPair
from electionguard.encrypt import EncryptionMediator

from electionguard_verify.verify import verify_ballot

import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory
from electionguard_tools.strategies.elgamal import elgamal_keypairs


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
