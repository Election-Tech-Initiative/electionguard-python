from typing import Any
from electionguard import PlaintextTally
from electionguard.manifest import Manifest, get_i8n_value
from electionguard.tally import PlaintextTallySelection
from electionguard_gui.models.election_dto import ElectionDto


def get_plaintext_ballot_report(
    election: ElectionDto, plaintext_ballot: PlaintextTally
) -> dict[str, Any]:
    manifest = election.get_manifest()
    selection_names = manifest.get_selection_names("en")
    contest_names = manifest.get_contest_names()
    selection_write_ins = _get_candidate_write_ins(manifest)
    parties = _get_selection_parties(manifest)
    tally_report = {}
    for tally_contest in plaintext_ballot.contests.values():
        contest_name = contest_names.get(tally_contest.object_id, "n/a")
        # non-write-in selections
        non_write_in_selections = [
            selection
            for selection in tally_contest.selections.values()
            if not selection_write_ins[selection.object_id]
        ]
        non_write_in_total = sum(
            [selection.tally for selection in non_write_in_selections]
        )
        non_write_in_selections_report = _get_selections_report(
            non_write_in_selections, selection_names, parties, non_write_in_total
        )

        # write-in selections
        write_ins_total = sum(
            [
                selection.tally
                for selection in tally_contest.selections.values()
                if selection_write_ins[selection.object_id]
            ]
        )

        tally_report[contest_name] = {
            "selections": non_write_in_selections_report,
            "nonWriteInTotal": non_write_in_total,
            "writeInTotal": write_ins_total,
        }
    return tally_report


def _get_selection_parties(manifest: Manifest) -> dict[str, str]:
    parties = {
        party.object_id: get_i8n_value(party.name, "en", "")
        for party in manifest.parties
    }
    candidates = {
        candidate.object_id: parties[candidate.party_id]
        for candidate in manifest.candidates
        if candidate.party_id is not None
    }
    contest_parties = {}
    for contest in manifest.contests:
        for selection in contest.ballot_selections:
            party = candidates.get(selection.candidate_id, "")
            contest_parties[selection.object_id] = party
    return contest_parties


def _get_candidate_write_ins(manifest: Manifest) -> dict[str, bool]:
    candidates = {
        candidate.object_id: candidate.is_write_in is True
        for candidate in manifest.candidates
    }
    contest_write_ins = {}
    for contest in manifest.contests:
        for selection in contest.ballot_selections:
            candidate_is_write_in = candidates[selection.candidate_id]
            contest_write_ins[selection.object_id] = candidate_is_write_in
    return contest_write_ins


def _get_selections_report(
    selections: list[PlaintextTallySelection],
    selection_names: dict[str, str],
    parties: dict[str, str],
    total: int,
) -> list:
    selections_report = []
    for selection in selections:
        selection_name = selection_names[selection.object_id]
        party = parties.get(selection.object_id, "")
        percent: float = (
            (float(selection.tally) / total) if selection.tally else float(0)
        )
        selections_report.append(
            {
                "name": selection_name,
                "tally": selection.tally,
                "party": party,
                "percent": percent,
            }
        )
    return selections_report
