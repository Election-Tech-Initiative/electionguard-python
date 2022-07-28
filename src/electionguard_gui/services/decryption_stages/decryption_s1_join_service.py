from typing import List
from pymongo.database import Database
from electionguard.ballot import BallotBoxState, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest, Manifest
from electionguard.scheduler import Scheduler
from electionguard.tally import CiphertextTally

from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services.decryption_stages.decryption_stage_base import (
    DecryptionStageBase,
)


class DecryptionS1JoinService(DecryptionStageBase):
    """Responsible for the 1st stage during a decryption were guardians join the decryption"""

    def run(self, db: Database, decryption: DecryptionDto) -> None:
        current_user_id = self._auth_service.get_required_user_id()
        self._log.debug(f"{current_user_id} decrypting  {decryption.decryption_id}")
        election = self._election_service.get(db, decryption.election_id)
        manifest = election.get_manifest()
        context = election.get_context()

        guardian = self._guardian_service.load_guardian_from_decryption(
            current_user_id, decryption
        )
        ballots = self._ballot_upload_service.get_ballots(db, election.id)
        spoiled_ballots = [
            ballot for ballot in ballots if ballot.state == BallotBoxState.SPOILED
        ]
        ciphertext_tally = get_tally(manifest, context, ballots)
        decryption_share = guardian.compute_tally_share(ciphertext_tally, context)
        if decryption_share is None:
            raise Exception("No decryption_shares found")
        ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
        if ballot_shares is None:
            raise Exception("No ballot shares found")

        self._decryption_service.append_guardian_joined(
            db,
            decryption.decryption_id,
            current_user_id,
            decryption_share,
            ballot_shares,
        )
        self._decryption_service.notify_changed(db, decryption.decryption_id)


def get_tally(
    manifest: Manifest,
    context: CiphertextElectionContext,
    ballots: List[SubmittedBallot],
) -> CiphertextTally:
    internal_manifest = InternalManifest(manifest)

    tally = CiphertextTally(
        "election-results",
        internal_manifest,
        context,
    )
    ballot_tuples = [(None, ballot) for ballot in ballots]
    with Scheduler() as scheduler:
        tally.batch_append(ballot_tuples, scheduler)
    return tally
