from os import environ
from sys import exit
from pymongo import MongoClient
from pymongo.database import Database


class DbService:
    """Responsible for instantiating a database"""

    DB_PASSWORD_KEY = "EG_DB_PASSWORD"
    DB_HOST_KEY = "EG_DB_HOST"
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 27017
    DEFAULT_USERNAME = "root"

    _db_password: str
    _db_host: str

    def __init__(self) -> None:
        self._db_password = get_param(self.DB_PASSWORD_KEY)
        self._db_host = get_param_or_default(self.DB_HOST_KEY, self.DEFAULT_HOST)

    def get_db(self) -> Database:
        client: MongoClient = MongoClient(
            self._db_host,
            self.DEFAULT_PORT,
            username=self.DEFAULT_USERNAME,
            password=self._db_password,
        )
        db: Database = client.ElectionGuardDb
        return db


def get_param(param_name: str) -> str:
    try:
        return environ[param_name]
    except KeyError:
        print(f"The environment variable {param_name} is not set.")
        exit(1)


def get_param_or_default(param_name: str, default: str) -> str:
    try:
        return environ[param_name]
    except KeyError:
        return default
