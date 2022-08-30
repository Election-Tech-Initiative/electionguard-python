from typing import Any, Optional
from datetime import datetime
from electionguard.election import CiphertextElectionContext
from electionguard.encrypt import EncryptionDevice
from electionguard.guardian import GuardianRecord
from electionguard.manifest import Manifest
from electionguard.serialize import from_list_raw, from_raw

from electionguard_gui.eel_utils import utc_to_str


# pylint: disable=too-many-instance-attributes
class ElectionDto:
    """Responsible for serializing to the front-end GUI and providing helper functions to Python."""

    id: str
    election_name: Optional[str]
    key_ceremony_id: Optional[str]
    guardians: Optional[int]
    quorum: Optional[int]
    manifest: Optional[dict[str, Any]]
    context: Optional[str]
    constants: Optional[int]
    guardian_records: Optional[str]
    encryption_package_file: Optional[str]
    election_url: Optional[str]
    ballot_uploads: list[dict[str, Any]]
    decryptions: list[dict[str, Any]]
    created_by: Optional[str]
    created_at_utc: Optional[datetime]
    created_at_str: str

    def __init__(self, election: dict[str, Any]):
        self.id = str(election.get("_id"))
        self.election_name = election.get("election_name")
        self.key_ceremony_id = election.get("key_ceremony_id")
        self.guardians = election.get("guardians")
        self.quorum = election.get("quorum")
        self.manifest = election.get("manifest")
        self.context = election.get("context")
        self.constants = election.get("constants")
        self.guardian_records = election.get("guardian_records")
        self.encryption_package_file = election.get("encryption_package_file")
        self.election_url = election.get("election_url")
        self.ballot_uploads = _get_list(election, "ballot_uploads")
        self.decryptions = _get_list(election, "decryptions")
        self.created_by = election.get("created_by")
        self.created_at_utc = election.get("created_at")
        self.created_at_str = utc_to_str(election.get("created_at"))

    def to_id_name_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
        }

    def _get_manifest_field(self, field: str) -> Any:
        return self.manifest.get(field) if self.manifest else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "election_name": self.election_name,
            "guardians": self.guardians,
            "quorum": self.quorum,
            "election_url": self.election_url,
            "manifest": {
                "name": self._get_manifest_field("name"),
                "scope": self._get_manifest_field("scope"),
                "geopolitical_units": self._get_manifest_field("geopolitical_units"),
                "parties": self._get_manifest_field("parties"),
                "candidates": self._get_manifest_field("candidates"),
                "contests": self._get_manifest_field("contests"),
                "ballot_styles": self._get_manifest_field("ballot_styles"),
            },
            "ballot_uploads": [
                {
                    "location": ballot_upload["location"],
                    "ballot_count": ballot_upload["ballot_count"],
                    "created_at": utc_to_str(ballot_upload.get("created_at")),
                }
                for ballot_upload in self.ballot_uploads
            ],
            "decryptions": [
                {
                    "decryption_id": decryption["decryption_id"],
                    "name": decryption["name"],
                    "created_at": utc_to_str(decryption.get("created_at")),
                }
                for decryption in self.decryptions
            ],
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }

    def get_manifest(self) -> Manifest:
        if not self.manifest:
            raise Exception("No manifest found")
        return from_raw(Manifest, self.manifest["raw"])

    def get_context(self) -> CiphertextElectionContext:
        if not self.context:
            raise Exception("No context found")
        return from_raw(CiphertextElectionContext, self.context)

    def get_encryption_devices(self) -> list[EncryptionDevice]:
        return [
            EncryptionDevice(
                ballot_upload["device_id"],
                ballot_upload["session_id"],
                ballot_upload["launch_code"],
                ballot_upload["location"],
            )
            for ballot_upload in self.ballot_uploads
        ]

    def get_guardian_records(self) -> list[GuardianRecord]:
        if not self.guardian_records:
            raise Exception("No guardian records found")
        return from_list_raw(GuardianRecord, self.guardian_records)

    def get_guardian_sequence_order(self, guardian_id: str) -> int:
        for record in self.get_guardian_records():
            if record.guardian_id == guardian_id:
                return record.sequence_order
        raise Exception("Guardian not found")

    def sum_ballots(self) -> int:
        return sum(ballot["ballot_count"] for ballot in self.ballot_uploads)


def _get_list(election: dict[str, Any], name: str) -> list:
    value = election.get(name)
    if value:
        return list(value)
    return []
