import logging
from typing import Any
from electionguard.logs import (
    log_critical,
    log_debug,
    log_error,
    log_info,
    log_warning,
    LOG,
)
from electionguard_gui.services.service_base import ServiceBase


class EelLogService(ServiceBase):
    """A facade for logging. Currently this simply writes to the console without using log levels, but
    this may eventually be used to log to a file or database."""

    def __init__(self) -> None:
        LOG.set_stream_log_level(logging.DEBUG)

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
    def error(self, message: str, *args: Any, **kwargs: Any) -> None:
        log_error(message, *args, **kwargs)

    # pylint: disable=no-self-use
    def fatal(self, message: str, *args: Any, **kwargs: Any) -> None:
        log_critical(message, *args, **kwargs)
