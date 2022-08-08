from typing import Any
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
    election_name: str
    key_ceremony_id: str
    guardians: int
    quorum: int
    manifest: dict[str, Any]
    context: str
    constants: int
    guardian_records: str
    encryption_package_file: str
    election_url: str
    ballot_uploads: list[dict[str, Any]]
    decryptions: list[dict[str, Any]]
    created_by: str
    created_at_utc: datetime
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
        self.ballot_uploads = election.get("ballot_uploads")
        self.decryptions = election.get("decryptions")
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
            "ballot_uploads": self.ballot_uploads,
            "decryptions": self.decryptions,
            "created_by": self.created_by,
            "created_at": self.created_at_str,
        }

    def get_manifest(self) -> Manifest:
        return from_raw(Manifest, self.manifest["raw"])

    def get_context(self) -> CiphertextElectionContext:
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
        return from_list_raw(GuardianRecord, self.guardian_records)
