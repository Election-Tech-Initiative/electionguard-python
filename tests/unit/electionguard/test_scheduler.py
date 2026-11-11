# pylint: disable=consider-using-with
from multiprocessing import Pool
from unittest.mock import patch

from tests.base_test_case import BaseTestCase

from electionguard.scheduler import Scheduler, use_scheduler


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
        self.assertIsInstance(result, list)
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
        self.assertIsInstance(result, list)

        # verify closing the poll catches the value error
        process_pool.close()

        result = subject.safe_map(process_pool, _callable, [1])
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)

        subject.close()

    @patch("electionguard.scheduler.ThreadPool")
    @patch("electionguard.scheduler.ProcessPool")
    def test_context_manager_opens_pools_once(self, process_pool, thread_pool):
        # Act
        with Scheduler():
            pass

        # Assert
        process_pool.assert_called_once()
        thread_pool.assert_called_once()
        process_pool.return_value.close.assert_called_once()
        thread_pool.return_value.close.assert_called_once()

    @patch("electionguard.scheduler.ThreadPool")
    @patch("electionguard.scheduler.ProcessPool")
    def test_use_scheduler_closes_only_schedulers_it_creates(
        self, process_pool, _thread_pool
    ):
        # Arrange
        existing = Scheduler()

        # Act
        with use_scheduler(existing) as scheduler:
            self.assertIs(scheduler, existing)
        with use_scheduler(None) as scheduler:
            self.assertIsNot(scheduler, existing)

        # Assert
        self.assertEqual(process_pool.call_count, 2)
        process_pool.return_value.close.assert_called_once()
