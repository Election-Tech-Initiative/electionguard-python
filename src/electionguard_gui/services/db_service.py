from pymongo import MongoClient
from pymongo.database import Database
from electionguard_gui.services.configuration_service import (
    ConfigurationService,
)
from electionguard_gui.services.eel_log_service import EelLogService

from electionguard_gui.services.service_base import ServiceBase


class DbService(ServiceBase):
    """Responsible for instantiating a database"""

    log_service: EelLogService

    def __init__(
        self, log_service: EelLogService, config_service: ConfigurationService
    ) -> None:
        self.log_service = log_service
        self._db_password = config_service.get_db_password()
        self._db_host = config_service.get_db_host(self.DEFAULT_HOST)

    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 27017
    DEFAULT_USERNAME = "root"

    _db_password: str
    _db_host: str

    def get_db(self) -> Database:
        client: MongoClient = MongoClient(
            self._db_host,
            self.DEFAULT_PORT,
            username=self.DEFAULT_USERNAME,
            password=self._db_password,
        )
        db: Database = client.ElectionGuardDb
        return db

    def verify_db_connection(self) -> None:
        self.log_service.debug("Verifying database connection")
        db = self.get_db()
        db.list_collections()
