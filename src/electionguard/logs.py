import inspect
import logging
import os.path
import sys
from typing import Any, List, Tuple
from logging.handlers import RotatingFileHandler

from .singleton import Singleton

FORMAT = "[%(process)d:%(asctime)s]:%(levelname)s:%(message)s"


class ElectionGuardLog(Singleton):
    """
    A singleton log for the library
    """

    __logger: logging.Logger

    def __init__(self) -> None:
        super().__init__()

        self.__logger = logging.getLogger("electionguard")
        self.__logger.addHandler(get_stream_handler())

    @staticmethod
    def __get_call_info() -> Tuple[str, str, int]:
        stack = inspect.stack()

        # stack[0]: __get_call_info
        # stack[1]: __formatted_message
        # stack[2]: (log method, e.g. "warn")
        # stack[3]: Singleton
        # stack[4]: caller <-- we want this

        filename = stack[4][1]
        line = stack[4][2]
        funcname = stack[4][3]

        return filename, funcname, line

    def __formatted_message(self, message: str) -> str:
        filename, funcname, line = self.__get_call_info()
        message = f"{os.path.basename(filename)}.{funcname}:#L{line}: {message}"
        return message

    def add_handler(self, handler: logging.Handler) -> None:
        """
        Adds a logger handler
        """
        self.__logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler) -> None:
        """
        Removes a logger handler
        """
        self.__logger.removeHandler(handler)

    def handlers(self) -> List[logging.Handler]:
        """
        Returns all logging handlers
        """
        return self.__logger.handlers

    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a debug message
        """
        self.__logger.debug(self.__formatted_message(message), *args, **kwargs)

    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a info message
        """
        self.__logger.info(self.__formatted_message(message), *args, **kwargs)

    def warn(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a warning message
        """
        self.__logger.warning(self.__formatted_message(message), *args, **kwargs)

    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a error message
        """
        self.__logger.error(self.__formatted_message(message), *args, **kwargs)

    def critical(self, message: str, *args: Any, **kwargs: Any) -> None:
        """
        Logs a critical message
        """
        self.__logger.critical(self.__formatted_message(message), *args, **kwargs)


def get_stream_handler() -> logging.StreamHandler:
    """
    Get a Stream Handler, sends only warnings and errors to stdout.
    """
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(logging.Formatter(FORMAT))
    return stream_handler


def get_file_handler() -> logging.FileHandler:
    """
    Get a File System Handler, sends verbose logging to a file, `electionguard.log`.
    When that file gets too large, the logs will rotate, creating files with names
    like `electionguard.log.1`.
    """

    # TODO: add file compression, save a bunch of space.
    #   https://medium.com/@rahulraghu94/overriding-pythons-timedrotatingfilehandler-to-compress-your-log-files-iot-c766a4ace240 # pylint: disable=line-too-long
    file_handler = RotatingFileHandler(
        "electionguard.log", "a", maxBytes=10_000_000, backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FORMAT))
    return file_handler


LOG = ElectionGuardLog()


def log_add_handler(handler: logging.Handler) -> None:
    """
    Adds a handler to the logger
    """
    LOG.add_handler(handler)


def log_remove_handler(handler: logging.Handler) -> None:
    """
    Removes a handler from the logger
    """
    LOG.remove_handler(handler)


def log_handlers() -> List[logging.Handler]:
    """
    Returns all logger handlers
    """
    return LOG.handlers()


def log_debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a debug message to the console and the file log.
    """
    LOG.debug(msg, *args, **kwargs)


def log_info(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs an information message to the console and the file log.
    """
    LOG.info(msg, *args, **kwargs)


def log_warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a warning message to the console and the file log.
    """
    LOG.warn(msg, *args, **kwargs)


def log_error(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs an error message to the console and the file log.
    """
    LOG.error(msg, *args, **kwargs)


def log_critical(msg: str, *args: Any, **kwargs: Any) -> None:
    """
    Logs a critical message to the console and the file log.
    """
    LOG.critical(msg, *args, **kwargs)
