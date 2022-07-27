from typing import Any
from datetime import datetime

from electionguard_gui.eel_utils import utc_to_str
from electionguard_gui.services.authorization_service import AuthorizationService


# pylint: disable=too-many-instance-attributes
class DecryptionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    decryption_id: str
    election_id: str
    election_name: str
    guardians: int
    decryption_name: str
    guardians_joined: list[str]
    can_join: bool
    created_by: str
    created_at_utc: datetime
    created_at_str: str

    def __init__(self, decryption: Any):
        self.decryption_id = str(decryption["_id"])
        self.election_id = decryption["election_id"]
        self.election_name = decryption["election_name"]
        self.guardians = decryption["guardians"]
        self.decryption_name = decryption["decryption_name"]
        self.guardians_joined = decryption["guardians_joined"]
        self.created_by = decryption["created_by"]
        self.created_at_utc = decryption["created_at"]
        self.created_at_str = utc_to_str(decryption["created_at"])
        self.can_join = False

    def get_status(self) -> str:
        if len(self.guardians_joined) < self.guardians:
            return "waiting for guardians"
        return "decryption complete"

    def to_id_name_dict(self) -> dict[str, Any]:
        return {
            "id": self.decryption_id,
            "decryption_name": self.decryption_name,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "decryption_id": self.decryption_id,
            "election_id": self.election_id,
            "election_name": self.election_name,
            "decryption_name": self.decryption_name,
            "guardians_joined": self.guardians_joined,
            "status": self.get_status(),
            "completed_at_str": None,
            "can_join": self.can_join,
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }

    def set_can_join(self, auth_service: AuthorizationService) -> None:
        user_id = auth_service.get_user_id()
        already_joined = user_id in self.guardians_joined
        is_admin = auth_service.is_admin()
        self.can_join = not already_joined and not is_admin
