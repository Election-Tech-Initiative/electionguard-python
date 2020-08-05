from __future__ import annotations
from contextlib import AbstractContextManager
from multiprocessing import Pool as ProcessPool
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.pool import Pool
from psutil import cpu_count
import traceback
from typing import Any, Callable, Iterable, List

from .logs import log_warning
from .singleton import Singleton
from .utils import T


class Scheduler(Singleton, AbstractContextManager):
    """
    Worker that wraps Multprocessing and allows 
    for shared context or spawning processes.
    Implemented as a singleton to guarantee there is only one set
    of tread and process pools in use throughout the library.
    Also implements the [Context Manager Protocol](https://docs.python.org/3.8/library/stdtypes.html#typecontextmanager)
    """

    __process_pool: Pool
    __thread_pool: Pool

    def __init__(self) -> None:
        super(Scheduler, self).__init__()
        self._open()

    def __enter__(self) -> Scheduler:
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

    def close(self) -> None:
        """Close pools"""
        self.__process_pool.close()
        self.__thread_pool.close()

    def cpu_count(self) -> int:
        """Get CPU count"""
        return int(cpu_count(logical=False))

    def schedule(
        self,
        task: Callable,
        arguments: Iterable[Iterable[Any]],
        with_shared_resources: bool = False,
    ) -> List[T]:
        """
        Schedule tasks with list of arguments
        :param task: the callable task to execute
        :param arguments: the list of lists passed to the task using starmap
        :param with_shared_resources: flag to use threads instead of processes
                                      allowing resources to be shared.  note
                                      when using the threadpool, execution is bound
                                      by default to the [global interpreter lock](https://docs.python.org/3.8/glossary.html#term-global-interpreter-lock)
        """
        if with_shared_resources:
            return self.safe_starmap(self.__thread_pool, task, arguments)
        return self.safe_starmap(self.__process_pool, task, arguments)

    def safe_starmap(
        self, pool: Pool, task: Callable, arguments: Iterable[Iterable[Any]]
    ) -> List[T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.starmap(task, arguments)
        except ValueError as e:
            log_warning(
                f"safe_starmap({task}, {arguments}) exception ValueError({str(e)})"
            )
            return []
        except Exception:
            log_warning(
                f"safe_starmap({task}, {arguments}) failed with \n {traceback.format_exc()}"
            )
            return []

    def safe_map(self, pool: Pool, task: Callable, arguments: Iterable[Any]) -> List[T]:
        """Safe wrapper around starmap to ensure pool is open"""
        try:
            return pool.map(task, arguments)
        except ValueError as e:
            log_warning(f"safe_map({task}, {arguments}) exception ValueError({str(e)})")
            return []
        except Exception:
            log_warning(
                f"safe_starmap({task}, {arguments}) failed with \n {traceback.format_exc()}"
            )
            return []
