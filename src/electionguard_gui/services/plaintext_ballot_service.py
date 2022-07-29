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
        contest_name = contest_names.get(tally_contest.object_id, "n/a")
        selections_report = []
        selections = list(iter(tally_contest.selections.values()))
        total = float(sum([selection.tally for selection in selections]))
        for selection in selections:
            selection_name = selection_names[selection.object_id]
            percent: float = (
                (float(selection.tally) / total) if selection.tally else float(0)
            )
            selections_report.append(
                {
                    "name": selection_name,
                    "tally": selection.tally,
                    "percent": percent,
                }
            )
        tally_report[contest_name] = {
            "selections": selections_report,
            "total": total,
        }
    return tally_report
