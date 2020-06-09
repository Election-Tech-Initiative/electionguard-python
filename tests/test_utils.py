from unittest import TestCase
from datetime import datetime

from electionguard.utils import to_ticks


class TestUtils(TestCase):
    def test_conversion_to_ticks(self):
        # Act
        ticks = to_ticks(datetime.utcnow())

        self.assertIsNotNone(ticks)
        self.assertGreater(ticks, 0)
