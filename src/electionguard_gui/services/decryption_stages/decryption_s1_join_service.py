from pymongo.database import Database
import eel
from electionguard.ballot import BallotBoxState

from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services.decryption_stages.decryption_stage_base import (
    DecryptionStageBase,
    get_tally,
)


class DecryptionS1JoinService(DecryptionStageBase):
    """Responsible for the 1st stage during a decryption were guardians join the decryption"""

    def run(self, db: Database, decryption: DecryptionDto) -> None:
        _update_decrypt_status("Starting tally")
        current_user_id = self._auth_service.get_required_user_id()
        self._log.info(f"S1: {current_user_id} decrypting  {decryption.decryption_id}")
        election = self._election_service.get(db, decryption.election_id)
        manifest = election.get_manifest()
        context = election.get_context()

        guardian = self._guardian_service.load_guardian_from_decryption(
            current_user_id, decryption
        )
        ballots = self._ballot_upload_service.get_ballots(
            db, election.id, _update_decrypt_status
        )
        _update_decrypt_status("Calculating tally")
        self._log.debug(f"getting tally for {len(ballots)} ballots")
        ciphertext_tally = get_tally(manifest, context, ballots, False)
        self._log.debug("computing tally share")
        decryption_share = guardian.compute_tally_share(ciphertext_tally, context)
        if decryption_share is None:
            raise Exception("No decryption_shares found")

        _update_decrypt_status("Calculating spoiled ballots")
        self._log.debug("decrypting spoiled ballots")
        spoiled_ballots = [
            ballot for ballot in ballots if ballot.state == BallotBoxState.SPOILED
        ]
        ballot_shares = guardian.compute_ballot_shares(spoiled_ballots, context)
        if ballot_shares is None:
            raise Exception("No ballot shares found")
        guardian_key = guardian.share_key()

        _update_decrypt_status("Finalizing tally")
        self._decryption_service.append_guardian_joined(
            db,
            decryption.decryption_id,
            current_user_id,
            decryption_share,
            ballot_shares,
            guardian_key,
        )
        self._log.debug("Completed tally")
        self._decryption_service.notify_changed(db, decryption.decryption_id)


def _update_decrypt_status(status: str) -> None:
    # pylint: disable=no-member
    eel.update_decrypt_status(status)
