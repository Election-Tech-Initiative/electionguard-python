

from .ballot import CiphertextBallot
from .election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)

from .logs import log_warning

def ballot_is_valid_for_election(
    ballot: CiphertextBallot,
    metadata: InternalElectionDescription,
    encryption_context: CiphertextElectionContext,
) -> bool:
    """
    Determine if a ballot is valid for a given election
    """

    if not ballot_is_valid_for_style(ballot, metadata):
        return False

    if not ballot.is_valid_encryption(
        encryption_context.crypto_extended_base_hash,
        encryption_context.elgamal_public_key,
    ):
        log_warning(
            f"ballot_is_valid_for_election: mismatching ballot encryption {ballot.object_id}"
        )
        return False

    return True

def ballot_is_valid_for_style(
    ballot: CiphertextBallot, metadata: InternalElectionDescription
) -> bool:
    descriptions = metadata.get_contests_for(ballot.ballot_style)

    for description in descriptions:
        use_contest = None
        for contest in ballot.contests:
            if description.object_id == contest.object_id:
                use_contest = contest

            # verify the contest exists on the ballot
            if use_contest is None:
                log_warning(
                    f"ballot is not valid for style: missing contest {description.object_id}"
                )
                return False

            # verify the hash matches
            if contest.description_hash != description.crypto_hash():
                log_warning(
                    f"ballot is not valid for style: mismatched hash for contest {description.object_id}"
                )
                return False

            # verify the placeholder count
            if len(contest.ballot_selections) != len(
                description.ballot_selections
            ) + len(description.placeholder_selections):
                log_warning(
                    f"ballot is not valid for style: mismatched selection count for contest {description.object_id}"
                )
                return False

    return True