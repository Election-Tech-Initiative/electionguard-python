# pylint: disable=consider-using-with
from __future__ import annotations
import traceback
from typing import Any, TypeVar
from collections.abc import Callable, Iterable
from contextlib import AbstractContextManager, nullcontext
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.pool import Pool
from psutil import cpu_count

from .logs import log_warning
from .singleton import Singleton

_T = TypeVar("_T")


class Scheduler(Singleton, AbstractContextManager):
    """
    Worker that wraps Multprocessing and allows
    for shared context or spawning processes.
    Each instance owns its own thread and process pools, so close it when done:
    prefer the [Context Manager Protocol](https://docs.python.org/3/library/stdtypes.html#typecontextmanager)
    or `use_scheduler`. `Scheduler.get_instance()` returns a shared instance.
    """

    __process_pool: Pool
    __thread_pool: Pool

    def __init__(self) -> None:
        super().__init__()
        self._is_open = False
        self._open()

    def __enter__(self) -> Scheduler:
        if not self._is_open:
            self._open()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        self.close()

    def _open(self) -> None:
        """Open pools"""
        max_processes = cpu_count(logical=False)
        # Reserve one CPU for I/O bound tasks
        if max_processes > 2:
            max_processes = max_processes - 1
        self.__process_pool = ProcessPool(max_processes)
        self.__thread_pool = ThreadPool(max_processes)
        self._is_open = True

    def close(self) -> None:
        """Close pools"""
        if not self._is_open:
            return
        self.__process_pool.close()
        self.__thread_pool.close()
        self._is_open = False

    @staticmethod
    def cpu_count() -> int:
        """Get CPU count"""
        return int(cpu_count(logical=False))

    def schedule(
        self,
        task: Callable,
        arguments: Iterable[Iterable[Any]],
        with_shared_resources: bool = False,
    ) -> list[_T]:
        """
        Schedule tasks with list of arguments
        :param task: the callable task to execute
        :param arguments: the list of lists passed to the task using starmap
        :param with_shared_resources: flag to use threads instead of processes
            allowing resources to be shared.  note
            when using the threadpool, execution is bound
            by default to the [global interpreter lock]
            (https://docs.python.org/3.8/glossary.html#term-global-interpreter-lock)
        """
        if with_shared_resources:
            return self.safe_starmap(self.__thread_pool, task, arguments)
        return self.safe_starmap(self.__process_pool, task, arguments)

    @staticmethod
    def safe_starmap(
        pool: Pool, task: Callable, arguments: Iterable[Iterable[Any]]
    ) -> list[_T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.starmap(task, arguments)
        except ValueError as e:
            log_warning(
                f"safe_starmap({task}, {arguments}) exception ValueError({str(e)})"
            )
            return []
        except Exception:  # pylint: disable=broad-exception-caught
            log_warning(
                f"safe_starmap({task}, {arguments}) failed with \n {traceback.format_exc()}"
            )
            return []

    @staticmethod
    def safe_map(pool: Pool, task: Callable, arguments: Iterable[Any]) -> list[_T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.map(task, arguments)
        except ValueError as e:
            log_warning(f"safe_map({task}, {arguments}) exception ValueError({str(e)})")
            return []
        except Exception:  # pylint: disable=broad-exception-caught
            log_warning(
                f"safe_starmap({task}, {arguments}) failed with \n {traceback.format_exc()}"
            )
            return []


def use_scheduler(scheduler: Scheduler | None) -> AbstractContextManager[Scheduler]:
    """
    Use the given scheduler as is, or a new one that is closed when the block exits.
    """
    return nullcontext(scheduler) if scheduler else Scheduler()
