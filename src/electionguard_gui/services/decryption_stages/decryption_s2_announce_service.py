from pymongo.database import Database
import eel
from electionguard import DecryptionMediator
from electionguard.ballot import BallotBoxState
from electionguard.election_polynomial import LagrangeCoefficientsRecord
from electionguard_gui.models.decryption_dto import DecryptionDto
from electionguard_gui.services.decryption_stages.decryption_stage_base import (
    DecryptionStageBase,
    get_tally,
)


class DecryptionS2AnnounceService(DecryptionStageBase):
    """Responsible for the 2nd stage in decryptions where the admin announces guardian decryptions"""

    def should_run(self, db: Database, decryption: DecryptionDto) -> bool:
        is_admin = self._auth_service.is_admin()
        all_guardians_joined = len(decryption.guardians_joined) >= decryption.guardians
        is_completed = decryption.completed_at_utc is not None
        return is_admin and all_guardians_joined and not is_completed

    def run(self, db: Database, decryption: DecryptionDto) -> None:
        _update_decrypt_status("Starting tally")
        self._log.info(f"S2: Announcing decryption {decryption.decryption_id}")
        election = self._election_service.get(db, decryption.election_id)
        context = election.get_context()

        decryption_mediator = DecryptionMediator(
            "decryption-mediator",
            context,
        )
        decryption_shares = decryption.get_decryption_shares()
        share_count = len(decryption_shares)
        current_share = 1
        for decryption_share_dict in decryption_shares:
            _update_decrypt_status(f"Calculating share {current_share}/{share_count}")
            self._log.debug(f"announcing {decryption_share_dict.guardian_id}")
            guardian_sequence_number = election.get_guardian_sequence_order(
                decryption_share_dict.guardian_id
            )
            # coefficients will fail validation unless the key is a numeric encoded
            #       string of the guardian's sequence number
            decryption_share_dict.guardian_key.owner_id = str(guardian_sequence_number)
            decryption_mediator.announce(
                decryption_share_dict.guardian_key,
                decryption_share_dict.tally_share,
                decryption_share_dict.ballot_shares,
            )
            current_share += 1

        manifest = election.get_manifest()
        ballots = self._ballot_upload_service.get_ballots(
            db, election.id, _update_decrypt_status
        )
        spoiled_ballots = [
            ballot for ballot in ballots if ballot.state == BallotBoxState.SPOILED
        ]
        _update_decrypt_status("Calculating tally")
        self._log.debug(f"getting tally for {len(ballots)} ballots")
        ciphertext_tally = get_tally(manifest, context, ballots, False)
        self._log.debug("getting plaintext tally")
        plaintext_tally = decryption_mediator.get_plaintext_tally(
            ciphertext_tally, manifest
        )
        if plaintext_tally is None:
            raise Exception("No plaintext tally found")
        self._log.debug("getting plaintext spoiled ballots")
        _update_decrypt_status("Processing spoiled ballots")
        plaintext_spoiled_ballots = decryption_mediator.get_plaintext_ballots(
            spoiled_ballots, manifest
        )
        if plaintext_spoiled_ballots is None:
            raise Exception("No plaintext spoiled ballots found")

        _update_decrypt_status("Finalizing tally")

        lagrange_coefficients = _get_lagrange_coefficients(decryption_mediator)

        self._log.debug("setting decryption completed")
        self._decryption_service.set_decryption_completed(
            db,
            decryption.decryption_id,
            plaintext_tally,
            plaintext_spoiled_ballots,
            lagrange_coefficients,
            ciphertext_tally.publish(),
        )

        self._decryption_service.notify_changed(db, decryption.decryption_id)


def _get_lagrange_coefficients(
    decryption_mediator: DecryptionMediator,
) -> LagrangeCoefficientsRecord:
    return LagrangeCoefficientsRecord(decryption_mediator.get_lagrange_coefficients())


def _update_decrypt_status(status: str) -> None:
    # pylint: disable=no-member
    eel.update_decrypt_status(status)
