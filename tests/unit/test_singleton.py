from tests.base_test_case import BaseTestCase
from electionguard.singleton import Singleton


class TestSingleton(BaseTestCase):
    """Singleton tests"""

    def test_singleton(self):
        singleton = Singleton()
        same_instance = singleton.get_instance()
        self.assertIsNotNone(singleton)
        self.assertIsNotNone(same_instance)

    def test_singleton_when_not_initialized(self):
        instance = Singleton.get_instance()
        self.assertIsNotNone(instance)
