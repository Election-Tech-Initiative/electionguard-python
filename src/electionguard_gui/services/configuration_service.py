from os import environ
from sys import exit

DB_PASSWORD_KEY = "EG_DB_PASSWORD"
DB_HOST_KEY = "EG_DB_HOST"
IS_ADMIN_KEY = "EG_IS_ADMIN"


def get_db_password() -> str:
    return _get_param(DB_PASSWORD_KEY)


def get_db_host(default: str) -> str:
    return _get_param_or_default(DB_HOST_KEY, default)


def get_is_admin() -> bool:
    return _get_param_or_default(IS_ADMIN_KEY, "false").lower() == "true"


def _get_param(param_name: str) -> str:
    try:
        return environ[param_name]
    except KeyError:
        print(f"The environment variable {param_name} is not set.")
        exit(1)


def _get_param_or_default(param_name: str, default: str) -> str:
    try:
        return environ[param_name]
    except KeyError:
        return default
