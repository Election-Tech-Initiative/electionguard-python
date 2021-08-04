# pylint: disable=consider-using-with
from multiprocessing import Pool
from typing import List

from tests.base_test_case import BaseTestCase

from electionguard.scheduler import Scheduler


def _callable(data: int):
    return data


def _exception_callable(something: int):
    raise Exception


class TestScheduler(BaseTestCase):
    """Scheduler tests"""

    def test_schedule_callable_throws(self):
        # Arrange
        subject = Scheduler()

        # Act
        result = subject.schedule(_exception_callable, [list([1]), list([2])])

        # Assert
        self.assertIsNotNone(result)
        self.assertIsInstance(result, List)
        subject.close()

    def test_safe_map(self):
        # Arrange
        process_pool = Pool(1)
        subject = Scheduler()

        # Act
        result = subject.safe_map(process_pool, _callable, [1])
        self.assertEqual(result, [1])

        # verify exceptions are caught
        result = subject.safe_map(process_pool, _exception_callable, [1])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, List)

        # verify closing the poll catches the value error
        process_pool.close()

        result = subject.safe_map(process_pool, _callable, [1])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, List)

        subject.close()
