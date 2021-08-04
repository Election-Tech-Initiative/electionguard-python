import os
from unittest import TestCase
from unittest.mock import patch

from electionguard.constants import PrimeOption


class BaseTestCase(TestCase):
    """Base Test Case for overriding environment variables."""

    @classmethod
    def setUpClass(cls):
        """Set up class."""
        cls.env_patcher = patch.dict(
            os.environ, {"PRIME_OPTION": PrimeOption.TestOnly.value}
        )
        cls.env_patcher.start()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        """Tear down class."""
        super().tearDownClass()

        cls.env_patcher.stop()
