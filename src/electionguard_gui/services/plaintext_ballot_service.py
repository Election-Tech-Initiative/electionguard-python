from typing import Any
from electionguard import PlaintextTally
from electionguard_gui.models.election_dto import ElectionDto


def get_plaintext_ballot_report(
    election: ElectionDto, plaintext_ballot: PlaintextTally
) -> dict[str, Any]:
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
