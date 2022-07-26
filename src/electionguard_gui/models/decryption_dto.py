from typing import Any
from datetime import datetime

from electionguard_gui.eel_utils import utc_to_str


# pylint: disable=too-many-instance-attributes
class DecryptionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    decryption_id: str
    election_id: str
    election_name: str
    guardians: int
    decryption_name: str
    guardians_joined: list[str]
    created_by: str
    created_at_utc: datetime
    created_at_str: str

    def __init__(self, decryption: dict[str, Any]):
        self.decryption_id = str(decryption["_id"])
        self.election_id = decryption["election_id"]
        self.election_name = decryption["election_name"]
        self.guardians = decryption["guardians"]
        self.decryption_name = decryption["decryption_name"]
        self.guardians_joined = decryption["guardians_joined"]
        self.created_by = decryption["created_by"]
        self.created_at_utc = decryption["created_at"]
        self.created_at_str = utc_to_str(decryption["created_at"])

    def get_status(self) -> str:
        if len(self.guardians_joined) < self.guardians:
            return "waiting for guardians"
        return "decryption complete"

    def to_dict(self) -> dict[str, Any]:
        return {
            "decryption_id": self.decryption_id,
            "election_id": self.election_id,
            "election_name": self.election_name,
            "decryption_name": self.decryption_name,
            "guardians_joined": self.guardians_joined,
            "status": self.get_status(),
            "completed_at_str": None,
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }
