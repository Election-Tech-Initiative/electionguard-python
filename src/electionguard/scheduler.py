from multiprocessing import Pool as ProcessPool, cpu_count
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.pool import Pool
from typing import Any, Callable, Iterable, List

from .singleton import Singleton
from .utils import T


class Scheduler(Singleton):
    """Multiprocessing Worker using pool of workers"""

    __process_pool: Pool
    __thread_pool: Pool

    def __init__(self) -> None:
        super(Scheduler, self).__init__()
        self._open()

    def _open(self) -> None:
        """Open pools"""
        self.__process_pool = ProcessPool(cpu_count())
        self.__thread_pool = ThreadPool(cpu_count())

    def close(self) -> None:
        """Close pools"""
        self.__process_pool.close()
        self.__thread_pool.close()

    def cpu_count(self) -> int:
        """Get CPU count"""
        return cpu_count()

    def schedule(self, task: Callable, arguments: Iterable[Iterable[Any]]) -> List[T]:
        """Schedule tasks with list of arguments"""
        return self.safe_starmap(self.__process_pool, task, arguments)

    def schedule_simple(self, task: Callable, arguments: Iterable[Any]) -> List[T]:
        """Schedule tasks with list of arguments"""
        return self.safe_map(self.__process_pool, task, arguments)

    def schedule_threads(
        self, task: Callable, arguments: Iterable[Iterable[Any]]
    ) -> List[T]:
        """Schedule threaded tasks with list of argument"""
        return self.safe_starmap(self.__thread_pool, task, arguments)

    def schedule_threads_simple(
        self, task: Callable, arguments: Iterable[Any]
    ) -> List[T]:
        """Schedule threaded tasks with list of arguments"""
        return self.safe_map(self.__thread_pool, task, arguments)

    def safe_starmap(
        self, pool: Pool, task: Callable, arguments: Iterable[Iterable[Any]]
    ) -> List[T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.starmap(task, arguments)
        except (ValueError):
            self._open()
            return pool.starmap(task, arguments)

    def safe_map(self, pool: Pool, task: Callable, arguments: Iterable[Any]) -> List[T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.map(task, arguments)
        except (ValueError):
            self._open()
            return pool.map(task, arguments)
