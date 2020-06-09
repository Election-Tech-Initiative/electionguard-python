from unittest import TestCase

from electionguard.encrypt import EncryptionDevice

from electionguard.group import ZERO_MOD_Q, ONE_MOD_Q, TWO_MOD_Q

from electionguard.tracker import (
    tracker_hash_to_words,
    tracker_words_to_hash,
    get_rotating_tracker_hash,
    get_hash_for_device,
)


class TestTracker(TestCase):
    def test_tracker_hash_rotates(self):
        # Arrange
        device = EncryptionDevice("Location")
        ballot_hash_1 = ONE_MOD_Q
        ballot_hash_2 = TWO_MOD_Q
        timestamp_1 = 1000
        timestamp_2 = 2000

        # Act
        device_hash = get_hash_for_device(device.uuid, device.location)
        tracker_1_hash = get_rotating_tracker_hash(
            device_hash, timestamp_1, ballot_hash_1
        )
        tracker_2_hash = get_rotating_tracker_hash(
            device_hash, timestamp_2, ballot_hash_2
        )

        # Assert
        self.assertIsNotNone(device_hash)
        self.assertIsNotNone(tracker_1_hash)
        self.assertIsNotNone(tracker_2_hash)

        self.assertNotEqual(device_hash, ZERO_MOD_Q)
        self.assertNotEqual(tracker_1_hash, device_hash)
        self.assertNotEqual(tracker_2_hash, device_hash)
        self.assertNotEqual(tracker_1_hash, tracker_2_hash)

    def test_tracker_converts_to_words(self):
        # Arrange
        device = EncryptionDevice("Location")
        device_hash = get_hash_for_device(device.uuid, device.location)
        ballot_hash = ONE_MOD_Q
        ballot_hash_different = TWO_MOD_Q
        timestamp = 1000
        tracker_hash = get_rotating_tracker_hash(device_hash, timestamp, ballot_hash)
        tracker_hash_different = get_rotating_tracker_hash(
            device_hash, timestamp, ballot_hash_different
        )

        # Act
        device_words = tracker_hash_to_words(device_hash)
        tracker_words = tracker_hash_to_words(tracker_hash)
        tracker_different_words = tracker_hash_to_words(tracker_hash_different)
        tracker_hash_from_words = tracker_words_to_hash(tracker_words)

        # Assert
        self.assertIsNotNone(device_words)
        self.assertIsNotNone(tracker_words)
        self.assertNotEqual(device_words, tracker_words)
        self.assertNotEqual(tracker_different_words, tracker_words)
        self.assertEqual(tracker_hash, tracker_hash_from_words)
