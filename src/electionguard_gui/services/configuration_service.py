from os import environ
from sys import exit
from typing import Optional

DB_PASSWORD_KEY = "EG_DB_PASSWORD"
DB_HOST_KEY = "EG_DB_HOST"
IS_ADMIN_KEY = "EG_IS_ADMIN"
PORT_KEY = "EG_PORT"
MODE_KEY = "EG_MODE"
HOST_KEY = "EG_HOST"


class ConfigurationService:
    """Responsible for retrieving configuration values, generally from environment variables"""

    # 'chrome', 'electron', 'edge', 'custom', or 'none', see also https://github.com/ChrisKnott/Eel#app-options
    def get_mode(self) -> Optional[str]:
        mode = self._get_param_or_default(MODE_KEY, "chrome")
        return None if mode == "none" else mode

    def get_port(self) -> int:
        return int(self._get_param_or_default(PORT_KEY, "0"))

    def get_host(self) -> str:
        return str(self._get_param_or_default(HOST_KEY, "localhost"))

    def get_db_password(self) -> str:
        return self._get_param(DB_PASSWORD_KEY)

    def get_db_host(self, default: str) -> str:
        return self._get_param_or_default(DB_HOST_KEY, default)

    def get_is_admin(self) -> bool:
        return self._get_param_or_default(IS_ADMIN_KEY, "false").lower() == "true"

    # pylint: disable=no-self-use
    def _get_param(self, param_name: str) -> str:
        try:
            return environ[param_name]
        except KeyError:
            print(f"The environment variable {param_name} is not set.")
            exit(1)

    # pylint: disable=no-self-use
    def _get_param_or_default(self, param_name: str, default: str) -> str:
        try:
            return environ[param_name]
        except KeyError:
            return default
