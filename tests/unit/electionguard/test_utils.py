from datetime import datetime, timezone

from tests.base_test_case import BaseTestCase

from electionguard.utils import to_ticks


class TestUtils(BaseTestCase):
    """Utility tests"""

    def test_conversion_to_ticks_from_utc(self):
        # Act
        ticks = to_ticks(datetime.now(timezone.utc))

        self.assertIsNotNone(ticks)
        self.assertGreater(ticks, 0)

    def test_conversion_to_ticks_from_local(self):
        # Act
        ticks = to_ticks(datetime.now())

        self.assertIsNotNone(ticks)
        self.assertGreater(ticks, 0)

    def test_conversion_to_ticks_with_tz(self):
        # Arrange
        now = datetime.now()
        now_with_tz = (now).astimezone()
        now_utc_with_tz = now_with_tz.astimezone(timezone.utc)

        # Act
        ticks_now = to_ticks(now)
        ticks_local = to_ticks(now_with_tz)
        ticks_utc = to_ticks(now_utc_with_tz)

        # Assert
        self.assertIsNotNone(ticks_now)
        self.assertIsNotNone(ticks_local)
        self.assertIsNotNone(ticks_utc)

        # Ensure all three tick values are the same
        unique_ticks = set([ticks_now, ticks_local, ticks_utc])
        self.assertEqual(1, len(unique_ticks))
        self.assertTrue(ticks_now in unique_ticks)

    def test_conversion_to_ticks_produces_valid_epoch(self):
        # Arrange
        now = datetime.now()

        # Act
        ticks_now = to_ticks(now)
        now_from_ticks = datetime.fromtimestamp(ticks_now)

        # Assert
        # Values below seconds are dropped from the epoch
        self.assertEqual(now.replace(microsecond=0), now_from_ticks)
