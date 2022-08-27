from typing import Any, Dict, Optional
from datetime import datetime
from electionguard.decryption_share import DecryptionShare
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.serialize import from_raw
from electionguard.tally import PlaintextTally, PublishedCiphertextTally
from electionguard.type import BallotId
from electionguard_gui.eel_utils import utc_to_str
from electionguard_gui.services.authorization_service import AuthorizationService


class GuardianDecryptionShare:
    """A guardian's contribution to a section of a tally and the spoiled ballots"""

    def __init__(
        self,
        guardian_id: str,
        decryption_share_json: str,
        ballot_shares: dict[str, str],
        guardian_key_json: str,
    ):
        self.guardian_id = guardian_id
        self.guardian_key = from_raw(ElectionPublicKey, guardian_key_json)
        self.tally_share = from_raw(DecryptionShare, decryption_share_json)
        self.ballot_shares = {
            ballot_id: from_raw(DecryptionShare, ballot_share)
            for (ballot_id, ballot_share) in ballot_shares.items()
        }

    guardian_id: str
    tally_share: DecryptionShare
    ballot_shares: Dict[BallotId, Optional[DecryptionShare]]
    guardian_key: ElectionPublicKey


# pylint: disable=too-many-instance-attributes
class DecryptionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    decryption_id: str
    election_id: str
    election_name: Optional[str]
    ballot_upload_count: int
    ballot_count: int
    guardians: int
    quorum: int
    decryption_name: Optional[str]
    key_ceremony_id: Optional[str]
    guardians_joined: list[str]
    can_join: Optional[bool]
    decryption_shares: list[Any]
    plaintext_tally: Optional[str]
    plaintext_spoiled_ballots: dict[str, str]
    lagrange_coefficients: Optional[str]
    ciphertext_tally: Optional[str]
    completed_at_utc: Optional[datetime]
    completed_at_str: str
    created_by: Optional[str]
    created_at_utc: Optional[datetime]
    created_at_str: str

    def __init__(self, decryption: dict[str, Any]):
        self.decryption_id = str(decryption.get("_id"))
        self.election_id = str(decryption.get("election_id"))
        self.key_ceremony_id = decryption.get("key_ceremony_id")
        self.election_name = decryption.get("election_name")
        self.ballot_upload_count = _get_int(decryption, "ballot_upload_count", 0)
        self.ballot_count = _get_int(decryption, "ballot_count", 0)
        self.guardians = _get_int(decryption, "guardians", 0)
        self.quorum = _get_int(decryption, "quorum", 0)
        self.decryption_name = decryption.get("decryption_name")
        self.guardians_joined = _get_list(decryption, "guardians_joined")
        self.decryption_shares = _get_list(decryption, "decryption_shares")
        self.plaintext_tally = decryption.get("plaintext_tally")
        self.plaintext_spoiled_ballots = _get_dict(
            decryption, "plaintext_spoiled_ballots"
        )
        self.lagrange_coefficients = decryption.get("lagrange_coefficients")
        self.ciphertext_tally = decryption.get("ciphertext_tally")
        self.completed_at_utc = decryption.get("completed_at")
        self.completed_at_str = utc_to_str(decryption.get("completed_at"))
        self.created_by = decryption.get("created_by")
        self.created_at_utc = decryption.get("created_at")
        self.created_at_str = utc_to_str(decryption.get("created_at"))
        self.can_join = False

    def get_status(self) -> str:
        if len(self.guardians_joined) < self.guardians:
            return "waiting for all guardians to join"
        if self.completed_at_utc is None:
            return "performing decryption"
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
            "ballot_upload_count": self.ballot_upload_count,
            "ballot_count": self.ballot_count,
            "decryption_name": self.decryption_name,
            "guardians_joined": self.guardians_joined,
            "status": self.get_status(),
            "completed_at_str": self.completed_at_str,
            "spoiled_ballots": list(self.plaintext_spoiled_ballots.keys())
            if self.plaintext_spoiled_ballots
            else [],
            "can_join": self.can_join,
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }

    def get_decryption_shares(self) -> list[GuardianDecryptionShare]:
        return [
            GuardianDecryptionShare(
                ballot_share_dict["guardian_id"],
                ballot_share_dict["decryption_share"],
                ballot_share_dict["ballot_shares"],
                ballot_share_dict["guardian_key"],
            )
            for ballot_share_dict in self.decryption_shares
        ]

    def set_can_join(self, auth_service: AuthorizationService) -> None:
        user_id = auth_service.get_user_id()
        already_joined = user_id in self.guardians_joined
        is_admin = auth_service.is_admin()
        self.can_join = not already_joined and not is_admin

    def get_plaintext_tally(self) -> PlaintextTally:
        if not self.plaintext_tally:
            raise ValueError("No plaintext tally found")
        return from_raw(PlaintextTally, self.plaintext_tally)

    def get_plaintext_spoiled_ballots(self) -> list[PlaintextTally]:
        return [
            from_raw(PlaintextTally, tally)
            for tally in self.plaintext_spoiled_ballots.values()
        ]

    def get_lagrange_coefficients(self) -> LagrangeCoefficientsRecord:
        if not self.lagrange_coefficients:
            raise ValueError("No lagrange coefficients found")
        return from_raw(LagrangeCoefficientsRecord, self.lagrange_coefficients)

    def get_ciphertext_tally(self) -> PublishedCiphertextTally:
        if not self.ciphertext_tally:
            raise ValueError("No ciphertext tally found")
        return from_raw(PublishedCiphertextTally, self.ciphertext_tally)


def _get_list(decryption: dict[str, Any], name: str) -> list:
    value = decryption.get(name)
    if value:
        return list(value)
    return []


def _get_dict(decryption: dict[str, Any], name: str) -> dict:
    value = decryption.get(name)
    if value:
        return dict(value)
    return {}


def _get_int(decryption: dict[str, Any], name: str, default: int) -> int:
    value = decryption.get(name)
    if value:
        return int(value)
    return default
