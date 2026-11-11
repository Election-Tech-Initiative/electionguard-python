from datetime import datetime, UTC
from electionguard_gui.eel_utils import utc_to_str
from tests.base_test_case import BaseTestCase


class TestEelUtils(BaseTestCase):
    """Tests eel utils"""

    def test_utc_to_str_with_valid_utc_date(self):
        date = datetime(2020, 2, 3, 7, 10, 10, 0, tzinfo=UTC)
        result = utc_to_str(date)
        # this test may be run in different timezones, so we can't test for exact time
        self.assertRegex(result, "Feb [2-4], 2020 [0-9]{1,2}:[0-9]{2} [AP]M")

    def test_utc_to_str_with_empty(self):
        result = utc_to_str(None)
        self.assertEqual(result, "")
