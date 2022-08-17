from datetime import datetime
import logging
from os import path, makedirs
from typing import Any
from electionguard.logs import (
    get_file_handler,
    log_critical,
    log_debug,
    log_error,
    log_info,
    log_warning,
    LOG,
)
from electionguard_gui.services.directory_service import get_data_dir
from electionguard_gui.services.service_base import ServiceBase


class EelLogService(ServiceBase):
    """A facade for logging. Currently this simply writes to the console without using log levels, but
    this may eventually be used to log to a file or database."""

    def __init__(self) -> None:
        LOG.set_stream_log_level(logging.DEBUG)
        file_dir = path.join(get_data_dir(), "logs")
        makedirs(file_dir, exist_ok=True)
        now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        file_name = path.join(file_dir, f"electionguard-{now}.log")
        LOG.add_handler(get_file_handler(logging.DEBUG, file_name))

    def trace(self, message: str, *args: Any, **kwargs: Any) -> None:
        pass

    # pylint: disable=no-self-use
    def debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        log_debug(message, *args, **kwargs)

    # pylint: disable=no-self-use
    def info(self, message: str, *args: Any, **kwargs: Any) -> None:
        log_info(message, *args, **kwargs)

    # pylint: disable=no-self-use
    def warn(self, message: str, *args: Any, **kwargs: Any) -> None:
        log_warning(message, *args, **kwargs)

    # pylint: disable=no-self-use
    def error(self, message: str, exception: Exception) -> None:
        log_error(
            f"{message} '{exception}'",
            exc_info=1,
            extra={"exception": exception},
        )

    # pylint: disable=no-self-use
    def fatal(self, message: str, exception: Exception) -> None:
        log_critical(
            f"{message} '{str(exception)}'",
            exc_info=1,
            extra={"exception": exception},
        )
