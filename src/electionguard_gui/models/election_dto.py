from typing import Any


class ElectionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    def __init__(self, election: dict[str, Any]):
        self.id = str(election["_id"])
        self.election_name = election["election_name"]

    def to_id_name_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
        }
