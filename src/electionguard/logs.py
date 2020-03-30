import logging
from typing import Any

# Unified logging for the ElectionGuard core library: we're sending all logging info to a file on disk
# ("electionguard.log") and we're only sending errors and criticals to the console. When normally running
# unit tests, this will go to 'tests/electionguard.log'. When running Tox, it goes to the project root directory.

# TODO: Make this work if we're running ElectionGuard in multiple *processes* at the same time.

# Says the Python logging cookbook:
#     https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
# Although logging is thread-safe, and logging to a single file from multiple threads in a single process
# is supported, logging to a single file from multiple processes is not supported, because there is no
# standard way to serialize access to a single file across multiple processes in Python.

logging.basicConfig(
    filename="electionguard.log",
    level=logging.DEBUG,
    format="%(asctime)s:%(name)s:%(levelname)s:%(message)s",
    filemode="w"  # erase and overwrite the log file each time
)
__logger = logging.getLogger("electionguard")
__ch = logging.StreamHandler()
__ch.setLevel(logging.ERROR)
__ch.setFormatter(logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s"))
# create formatter and add it to the handlers
__logger.addHandler(__ch)


def log_debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a debug message to the console and the file log.
    """
    __logger.debug(msg, *args, **kwargs)


def log_info(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs an information message to the console and the file log.
    """
    __logger.info(msg, *args, **kwargs)


def log_warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a warning message to the console and the file log.
    """
    __logger.warning(msg, *args, **kwargs)


def log_error(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs an error message to the console and the file log.
    """
    __logger.error(msg, *args, **kwargs)


def log_critical(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a critical message to the console and the file log.
    """
    __logger.critical(msg, *args, **kwargs)


# these should only appear in the log file
log_debug("ElectionGuard log system starting (testing debug)")
log_info("ElectionGuard log system starting (testing info)")
log_warning("ElectionGuard log system starting (testing warning)")

# these should be in the log file and visible on the console
log_error("ElectionGuard log system starting (testing error)")
log_critical("ElectionGuard log system starting (testing critical)")
