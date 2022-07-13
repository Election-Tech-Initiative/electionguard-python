from datetime import datetime
from electionguard_gui.services.service_base import ServiceBase


class EelLogService(ServiceBase):
    """A facade for logging. Currently this simply writes to the console without using log levels, but
    this may eventually be used to log to a file or database."""

    # pylint: disable=no-self-use
    def _log(self, level: str, message: str) -> None:
        print(f"{datetime.now()} {level} {message}")

    def debug(self, message: str) -> None:
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        self._log("INFO ", message)

    def warn(self, message: str) -> None:
        self._log("WARN ", message)

    def error(self, e: Exception) -> None:
        self._log("ERROR", str(e))

    def fatal(self, message: str) -> None:
        self._log("FATAL", message)
