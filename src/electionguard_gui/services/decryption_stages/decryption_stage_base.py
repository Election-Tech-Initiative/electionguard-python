from abc import ABC
from typing import List
from pymongo.database import Database
from electionguard.ballot import SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest, Manifest
from electionguard.tally import CiphertextTally
from electionguard.scheduler import Scheduler

from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services.authorization_service import AuthorizationService
from electionguard_gui.services.ballot_upload_service import BallotUploadService
from electionguard_gui.services.db_service import DbService
from electionguard_gui.services.decryption_service import DecryptionService
from electionguard_gui.services.eel_log_service import EelLogService
from electionguard_gui.services.election_service import ElectionService
from electionguard_gui.services.guardian_service import GuardianService


class DecryptionStageBase(ABC):
    """Responsible for shared functionality across all decryption stages"""

    _log: EelLogService
    _db_service: DbService
    _decryption_service: DecryptionService
    _auth_service: AuthorizationService
    _guardian_service: GuardianService
    _election_service: ElectionService
    _ballot_upload_service: BallotUploadService

    def __init__(
        self,
        log_service: EelLogService,
        db_service: DbService,
        decryption_service: DecryptionService,
        auth_service: AuthorizationService,
        guardian_service: GuardianService,
        election_service: ElectionService,
        ballot_upload_service: BallotUploadService,
    ):
        self._db_service = db_service
        self._decryption_service = decryption_service
        self._auth_service = auth_service
        self._log = log_service
        self._guardian_service = guardian_service
        self._election_service = election_service
        self._ballot_upload_service = ballot_upload_service

    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    def should_run(self, db: Database, decryption: DecryptionDto) -> bool:
        return False

    def run(self, db: Database, decryption: DecryptionDto) -> None:
        pass


def get_tally(
    manifest: Manifest,
    context: CiphertextElectionContext,
    ballots: List[SubmittedBallot],
    should_validate: bool,
) -> CiphertextTally:
    internal_manifest = InternalManifest(manifest)

    tally = CiphertextTally(
        "election-results",
        internal_manifest,
        context,
    )
    ballot_tuples = [(None, ballot) for ballot in ballots]
    with Scheduler() as scheduler:
        tally.batch_append(ballot_tuples, should_validate, scheduler)
    return tally
