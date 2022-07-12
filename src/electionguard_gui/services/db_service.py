from pymongo import MongoClient
from pymongo.database import Database
from electionguard_gui.services.configuration_service import (
    get_db_host,
    get_db_password,
)

from electionguard_gui.services.service_base import ServiceBase


class DbService(ServiceBase):
    """Responsible for instantiating a database"""

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 27017
    DEFAULT_USERNAME = "root"

    _db_password: str
    _db_host: str

    def __init__(self) -> None:
        self._db_password = get_db_password()
        self._db_host = get_db_host(self.DEFAULT_HOST)

    def get_db(self) -> Database:
        client: MongoClient = MongoClient(
            self._db_host,
            self.DEFAULT_PORT,
            username=self.DEFAULT_USERNAME,
            password=self._db_password,
        )
        db: Database = client.ElectionGuardDb
        return db
