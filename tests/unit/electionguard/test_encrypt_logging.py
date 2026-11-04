from tests.base_test_case import BaseTestCase

from electionguard.elgamal import elgamal_keypair_from_secret
from electionguard.encrypt import EncryptionMediator
from electionguard.group import TWO_MOD_Q
from electionguard.utils import get_optional
import electionguard_tools.factories.ballot_factory as BallotFactory
import electionguard_tools.factories.election_factory as ElectionFactory


class TestEncryptLogging(BaseTestCase):
    """Encryption logging tests"""

    def test_encrypting_a_ballot_logs_nothing_at_info(self):
        # Arrange
        keypair = get_optional(elgamal_keypair_from_secret(TWO_MOD_Q))
        factory = ElectionFactory.ElectionFactory()
        internal_manifest, context = factory.get_fake_ciphertext_election(
            factory.get_fake_manifest(), keypair.public_key
        )
        encrypter = EncryptionMediator(
            internal_manifest, context, factory.get_encryption_device()
        )
        ballot = BallotFactory.BallotFactory().get_fake_ballot(internal_manifest)

        # Act & Assert
        # per-selection traces flooded the console when encrypting many ballots
        with self.assertNoLogs("electionguard", level="INFO"):
            self.assertIsNotNone(encrypter.encrypt(ballot))
