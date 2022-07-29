from typing import Any
import eel
from electionguard.tally import PlaintextTally
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.models.election_dto import ElectionDto
from electionguard_gui.services import (
    DecryptionService,
    ElectionService,
)


class ViewSpoiledBallotComponent(ComponentBase):
    """Responsible for functionality related to viewing a tally"""

    _decryption_service: DecryptionService
    _election_service: ElectionService

    def __init__(
        self, decryption_service: DecryptionService, election_service: ElectionService
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_spoiled_ballot)

    def get_plaintext_ballot_report(
        self, election: ElectionDto, plaintext_ballot: PlaintextTally
    ) -> Any:
        manifest = election.get_manifest()
        selection_names = manifest.get_selection_names("en")
        contest_names = manifest.get_contest_names()
        tally_report = {}
        for tally_contest in plaintext_ballot.contests.values():
            contest_name = contest_names.get(tally_contest.object_id)
            selections = {}
            for selection in tally_contest.selections.values():
                selection_name = selection_names[selection.object_id]
                selections[selection_name] = selection.tally
            tally_report[contest_name] = selections
        return tally_report

    def get_spoiled_ballot(
        self, decryption_id: str, spoiled_ballot_id: str
    ) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            self._log.debug(
                f"retrieving spoiled ballot '{decryption_id}'.{spoiled_ballot_id}"
            )
            decryption = self._decryption_service.get(db, decryption_id)
            election = self._election_service.get(db, decryption.election_id)
            spoiled_ballots = decryption.get_plaintext_spoiled_ballots()
            plaintext_tally = get_spoiled_ballot_by_id(
                spoiled_ballots, spoiled_ballot_id
            )
            tally_report = self.get_plaintext_ballot_report(election, plaintext_tally)
            result = {
                "election_id": election.id,
                "election_name": election.election_name,
                "decryption_name": decryption.decryption_name,
                "report": tally_report,
            }
            return eel_success(result)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)


def get_spoiled_ballot_by_id(
    spoiled_ballots: list[PlaintextTally], spoiled_ballot_id: str
) -> PlaintextTally:
    matches: list[PlaintextTally] = [
        ballot for ballot in spoiled_ballots if ballot.object_id == spoiled_ballot_id
    ]
    return next(iter(matches))
