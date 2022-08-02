from datetime import datetime, timezone
from electionguard_gui.eel_utils import utc_to_str
from tests.base_test_case import BaseTestCase


class TestEelUtils(BaseTestCase):
    """Tests eel utils"""

    def test_utc_to_str_with_valid_utc_date(self):
        date = datetime(2020, 2, 3, 7, 10, 10, 0, tzinfo=timezone.utc)
        result = utc_to_str(date)
        self.assertEqual(result, "Feb 3, 2020 2:10 AM")

    def test_utc_to_str_with_empty(self):
        result = utc_to_str(None)
        self.assertEqual(result, "")
