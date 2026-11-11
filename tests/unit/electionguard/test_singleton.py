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

    def test_singleton_instance_is_per_subclass(self):
        class First(Singleton):
            """First test subclass"""

        class Second(Singleton):
            """Second test subclass"""

        self.assertIsInstance(First.get_instance(), First)
        self.assertIsInstance(Second.get_instance(), Second)
        self.assertIs(First.get_instance(), First.get_instance())
