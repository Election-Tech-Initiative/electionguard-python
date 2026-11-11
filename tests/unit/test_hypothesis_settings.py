from hypothesis import settings

from tests.base_test_case import BaseTestCase


class TestHypothesisSettings(BaseTestCase):
    """The test session's default Hypothesis settings."""

    def test_default_profile_has_no_deadline(self):
        # Property tests check results, not timing. A per-example deadline makes
        # them fail with DeadlineExceeded on a slow or busy machine.
        self.assertIsNone(settings.default.deadline)
