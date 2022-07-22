from typing import Any
from datetime import datetime

from electionguard_gui.eel_utils import utc_to_str


class ElectionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    id: str
    election_name: str
    guardians: int
    quorum: int
    manifest: dict[str, Any]
    constants: int
    guardian_records: int
    created_by: str
    created_at_utc: datetime
    created_at_str: str

    def __init__(self, election: dict[str, Any]):
        self.id = str(election["_id"])
        self.election_name = election["election_name"]
        self.guardians = election["guardians"]
        self.quorum = election["quorum"]
        self.manifest = election["manifest"]
        self.constants = election["constants"]
        self.guardian_records = election["guardian_records"]
        self.created_by = election["created_by"]
        self.created_at_utc = election["created_at"]
        self.created_at_str = utc_to_str(election["created_at"])

    def to_id_name_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
            "guardians": self.guardians,
            "quorum": self.quorum,
            "manifest": {
                "name": self.manifest["name"],
                "scope": self.manifest["scope"],
                "geopolitical_units": self.manifest["geopolitical_units"],
                "parties": self.manifest["parties"],
                "candidates": self.manifest["candidates"],
                "contests": self.manifest["contests"],
                "ballot_styles": self.manifest["ballot_styles"],
            },
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }
