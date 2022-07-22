import json
from bson import ObjectId
from pydantic.json import pydantic_encoder
from pymongo.database import Database
from electionguard.constants import ElectionConstants
from electionguard.election import CiphertextElectionContext
from electionguard.guardian import GuardianRecord
from electionguard.manifest import Manifest
from electionguard_gui.models import KeyCeremonyDto, ElectionDto
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.service_base import ServiceBase


class ElectionService(ServiceBase):
    """Responsible for functionality related to elections"""

    _log: EelLogService

    def __init__(self, log_service: EelLogService) -> None:
        self._log = log_service

    def create_election(
        self,
        db: Database,
        election_name: str,
        key_ceremony: KeyCeremonyDto,
        manifest: Manifest,
        context: CiphertextElectionContext,
        constants: ElectionConstants,
        guardian_records: list[GuardianRecord],
    ) -> str:
        context_raw = json.dumps(context, default=pydantic_encoder)
        manifest_raw = json.dumps(manifest, default=pydantic_encoder)
        constants_raw = json.dumps(constants, default=pydantic_encoder)
        guardian_records_raw = json.dumps(guardian_records, default=pydantic_encoder)
        election = {
            "election_name": election_name,
            "key_ceremony_id": key_ceremony.id,
            "manifest": {
                "raw": manifest_raw,
                "name": manifest.get_name(),
                "scope": manifest.election_scope_id,
                "geopolitical_units": len(manifest.geopolitical_units),
                "parties": len(manifest.parties),
                "candidates": len(manifest.candidates),
                "contests": len(manifest.contests),
                "ballot_styles": len(manifest.ballot_styles),
            },
            "context": context_raw,
            "constants": constants_raw,
            "guardian_records": guardian_records_raw,
        }
        self._log.trace(f"inserting election: {election}")
        inserted_id = db.elections.insert_one(election).inserted_id
        return str(inserted_id)

    def get(self, db: Database, election_id: str) -> ElectionDto:
        election = db.elections.find_one({"_id": ObjectId(election_id)})
        if not election:
            raise Exception(f"Election not found: {election_id}")
        return ElectionDto(election)

    def get_all(self, db: Database) -> list[ElectionDto]:
        elections = db.elections.find()
        return [ElectionDto(election) for election in elections]
