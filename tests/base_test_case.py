import os
from unittest import TestCase
from unittest.mock import patch
from pytest import fixture
from pytest_mock import MockerFixture
from electionguard.constants import PrimeOption


class BaseTestCase(TestCase):
    """Base Test Case for overriding environment variables."""

    mocker: MockerFixture

    # pylint: disable=unused-private-member
    @fixture(autouse=True)
    def __inject_fixtures(self, mocker):
        self.mocker = mocker

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
