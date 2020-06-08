from typing import List, Dict
from electionguard.ballot import PlaintextBallot


def accumulate_plaintext_ballots(ballots: List[PlaintextBallot]) -> Dict[str, int]:
    """
    Internal helper function for testing: takes a list of plaintext ballots as input,
    digs into all of the individual selections and then accumulates them, using
    their `object_id` fields as keys. This function only knows what to do with
    `n_of_m` elections. It's not a general-purpose tallying mechanism for other
    election types.

    :param ballots: a list of plaintext ballots
    :return: a dict from selection object_id's to integer totals
    """
    tally: Dict[str, int] = {}
    for ballot in ballots:
        for contest in ballot.contests:
            for selection in contest.ballot_selections:
                assert (
                    not selection.is_placeholder_selection
                ), "Placeholder selections should not exist in the plaintext ballots"
                desc_id = selection.object_id
                if desc_id not in tally:
                    tally[desc_id] = 0
                # returns 1 or 0 for n-of-m ballot selections
                tally[desc_id] += selection.to_int()
    return tally
