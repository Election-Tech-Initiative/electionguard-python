import multiprocessing
import multiprocessing.pool
from multiprocessing.context import BaseContext

from typing import Any

from .singleton import Singleton


class NoDaemonProcess(multiprocessing.Process):
    daemon = False


class NoDaemonContext(BaseContext):
    Process = NoDaemonProcess


class GlobalProcessingPool(multiprocessing.pool.Pool):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["context"] = NoDaemonContext()
        super(GlobalProcessingPool, self).__init__(*args, **kwargs)


global CPU_POOL
CPU_POOL = GlobalProcessingPool(multiprocessing.cpu_count())
