from tests.base_test_case import BaseTestCase

from electionguard.group import ZERO_MOD_Q, ONE_MOD_Q, TWO_MOD_Q
from electionguard.ballot_code import (
    get_ballot_code,
    get_hash_for_device,
)

from electionguard_tools.factories.election_factory import ElectionFactory


class TestBallotCode(BaseTestCase):
    """Ballot code tests"""

    def test_rotate_ballot_code(self):
        # Arrange
        device = ElectionFactory.get_encryption_device()
        ballot_hash_1 = ONE_MOD_Q
        ballot_hash_2 = TWO_MOD_Q
        timestamp_1 = 1000
        timestamp_2 = 2000

        # Act
        device_hash = get_hash_for_device(
            device.device_id, device.session_id, device.launch_code, device.location
        )
        ballot_code_1 = get_ballot_code(device_hash, timestamp_1, ballot_hash_1)
        ballot_code_2 = get_ballot_code(device_hash, timestamp_2, ballot_hash_2)

        # Assert
        self.assertIsNotNone(device_hash)
        self.assertIsNotNone(ballot_code_1)
        self.assertIsNotNone(ballot_code_2)

        self.assertNotEqual(device_hash, ZERO_MOD_Q)
        self.assertNotEqual(ballot_code_1, device_hash)
        self.assertNotEqual(ballot_code_2, device_hash)
        self.assertNotEqual(ballot_code_1, ballot_code_2)
