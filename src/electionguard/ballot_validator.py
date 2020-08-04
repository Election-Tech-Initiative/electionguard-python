from .ballot import CiphertextBallot, CiphertextBallotContest, CiphertextBallotSelection
from .election import (
    CiphertextElectionContext,
    ContestDescriptionWithPlaceholders,
    InternalElectionDescription,
    SelectionDescription,
)

from .logs import log_warning


def ballot_is_valid_for_election(
    ballot: CiphertextBallot,
    metadata: InternalElectionDescription,
    context: CiphertextElectionContext,
) -> bool:
    """
    Determine if a ballot is valid for a given election
    """

    if not ballot_is_valid_for_style(ballot, metadata):
        return False

    if not ballot.is_valid_encryption(
        metadata.description_hash,
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        log_warning(
            f"ballot_is_valid_for_election: mismatching ballot encryption {ballot.object_id}"
        )
        return False

    return True


def selection_is_valid_for_style(
    selection: CiphertextBallotSelection, description: SelectionDescription
) -> bool:
    """
    Determine if selection is valid for ballot style
    :param selection: Ballot selection
    :param description: Selection description
    :return: Is valid
    """
    if selection.description_hash != description.crypto_hash():
        log_warning(
            f"ballot is not valid for style: mismatched selection description hash {selection.description_hash} for selection {description.object_id} hash {description.crypto_hash()}"
        )
        return False

    return True


def contest_is_valid_for_style(
    contest: CiphertextBallotContest, description: ContestDescriptionWithPlaceholders
) -> bool:
    """
    Determine if contest is valid for ballot style
    :param contest: Contest
    :param description: Contest description
    :return: Is valid
    """
    # verify the hash matches
    if contest.description_hash != description.crypto_hash():
        log_warning(
            f"ballot is not valid for style: mismatched description hash {contest.description_hash} for contest {description.object_id} hash {description.crypto_hash()}"
        )
        return False

    # verify the placeholder count
    if len(contest.ballot_selections) != len(description.ballot_selections) + len(
        description.placeholder_selections
    ):
        log_warning(
            f"ballot is not valid for style: mismatched selection count for contest {description.object_id}"
        )
        return False

    return True


def ballot_is_valid_for_style(
    ballot: CiphertextBallot, metadata: InternalElectionDescription
) -> bool:
    """
    Determine if ballot is valid for ballot style
    :param ballot: Ballot
    :param metadata: Internal election description
    :return: Is valid
    """
    descriptions = metadata.get_contests_for(ballot.ballot_style)

    for description in descriptions:
        use_contest = None
        for contest in ballot.contests:
            if description.object_id == contest.object_id:
                use_contest = contest
                break

        # verify the contest exists on the ballot
        if use_contest is None:
            log_warning(
                f"ballot is not valid for style: missing contest {description.object_id}"
            )
            return False

        if not contest_is_valid_for_style(use_contest, description):
            return False

        # verify the selection metadata
        for selection_description in description.ballot_selections:
            use_selection = None
            for selection in use_contest.ballot_selections:
                if selection_description.object_id == selection.object_id:
                    use_selection = selection
                    break

            if use_selection is None:
                log_warning(
                    f"ballot is not valid for style: missing selection {selection_description.object_id}"
                )
                return False

            if not selection_is_valid_for_style(use_selection, selection_description):
                return False

    return True
