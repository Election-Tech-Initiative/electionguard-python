from typing import Any
from electionguard import PlaintextTally
from electionguard.manifest import Manifest, get_i8n_value
from electionguard.tally import PlaintextTallySelection
from electionguard_gui.models.election_dto import ElectionDto


def get_plaintext_ballot_report(
    election: ElectionDto, plaintext_ballot: PlaintextTally
) -> list:
    manifest = election.get_manifest()
    selection_names = manifest.get_selection_names("en")
    contest_names = manifest.get_contest_names()
    selection_write_ins = _get_candidate_write_ins(manifest)
    parties = _get_selection_parties(manifest)
    tally_report = _get_tally_report(
        plaintext_ballot, selection_names, contest_names, selection_write_ins, parties
    )
    return tally_report


def _get_tally_report(
    plaintext_ballot: PlaintextTally,
    selection_names: dict[str, str],
    contest_names: dict[str, str],
    selection_write_ins: dict[str, bool],
    parties: dict[str, str],
) -> list:
    tally_report = []
    contests = plaintext_ballot.contests.values()
    for tally_contest in contests:
        selections = list(tally_contest.selections.values())
        contest_details = _get_contest_details(
            selections, selection_names, selection_write_ins, parties
        )
        contest_name = contest_names.get(tally_contest.object_id, "n/a")
        tally_report.append(
            {
                "name": contest_name,
                "details": contest_details,
            }
        )
    return tally_report


def _get_contest_details(
    selections: list[PlaintextTallySelection],
    selection_names: dict[str, str],
    selection_write_ins: dict[str, bool],
    parties: dict[str, str],
) -> dict[str, Any]:

    # non-write-in selections
    non_write_in_selections = [
        selection
        for selection in selections
        if not selection_write_ins[selection.object_id]
    ]
    non_write_in_total = sum([selection.tally for selection in non_write_in_selections])
    non_write_in_selections_report = _get_selections_report(
        non_write_in_selections, selection_names, parties, non_write_in_total
    )

    # write-in selections
    write_ins = [
        selection.tally
        for selection in selections
        if selection_write_ins[selection.object_id]
    ]
    any_write_ins = len(write_ins) > 0
    write_ins_total = sum(write_ins) if any_write_ins else None

    return {
        "selections": non_write_in_selections_report,
        "nonWriteInTotal": non_write_in_total,
        "writeInTotal": write_ins_total,
    }


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
    """
    Returns a dictionary where the key is a selection's object_id and the value is a boolean
    indicating whether the selection's candidate is marked as a write-in.
    """
    write_in_candidates = {
        candidate.object_id: candidate.is_write_in is True
        for candidate in manifest.candidates
    }
    contest_write_ins = {}
    for contest in manifest.contests:
        for selection in contest.ballot_selections:
            candidate_is_write_in = write_in_candidates[selection.candidate_id]
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
