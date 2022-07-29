from typing import Any
import eel
from electionguard_gui.eel_utils import eel_success
from electionguard_gui.components.component_base import ComponentBase
from electionguard_gui.services import (
    DecryptionService,
    ElectionService,
)


class ViewTallyComponent(ComponentBase):
    """Responsible for functionality related to viewing a tally"""

    _decryption_service: DecryptionService
    _election_service: ElectionService

    def __init__(
        self, decryption_service: DecryptionService, election_service: ElectionService
    ) -> None:
        self._decryption_service = decryption_service
        self._election_service = election_service

    def expose(self) -> None:
        eel.expose(self.get_tally)

    def get_tally(self, decryption_id: str) -> dict[str, Any]:
        try:
            db = self._db_service.get_db()
            self._log.debug(f"retrieving decryption '{decryption_id}'")
            decryption = self._decryption_service.get(db, decryption_id)
            election = self._election_service.get(db, decryption.election_id)
            manifest = election.get_manifest()
            plaintext_tally = decryption.get_plaintext_tally()

            selection_names = manifest.get_selection_names("en")
            contest_names = manifest.get_contest_names()

            tally_report = {}
            for tally_contest in plaintext_tally.contests.values():
                contest_name = contest_names.get(tally_contest.object_id)
                selections = {}
                for selection in tally_contest.selections.values():
                    selection_name = selection_names[selection.object_id]
                    selections[selection_name] = selection.tally
                tally_report[contest_name] = selections

            return eel_success(tally_report)
        # pylint: disable=broad-except
        except Exception as e:
            return self.handle_error(e)
