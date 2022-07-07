from pymongo import MongoClient
from pymongo.database import Database


class DbService:
    """Responsible for instantiating a database"""

    _db_password: str

    def __init__(self, db_password: str) -> None:
        self._db_password = db_password

    def get_db(self) -> Database:
        client: MongoClient = MongoClient(
            "localhost", 27017, username="root", password=self._db_password
        )
        db: Database = client.ElectionGuardDb
        return db
