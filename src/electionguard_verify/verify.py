from dataclasses import dataclass
from typing import Dict, Optional, List

from electionguard.ballot import CiphertextBallot, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.manifest import (
    InternalManifest,
    Manifest,
)
from electionguard.type import GuardianId
from electionguard.tally import PlaintextTally, CiphertextTally


@dataclass
class Verification:
    """
    Representation of a verification result with an optional message
    """

    verified: bool
    """Verification successful?"""
    message: Optional[str]


def verify_ballot(
    ballot: CiphertextBallot,
    manifest: Manifest,
    context: CiphertextElectionContext,
) -> Verification:
    """
    Method to verify the validity of a ballot
    """

    if not ballot.is_valid_encryption(
        manifest.crypto_hash(),
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        return Verification(
            False,
            message=f"verify_ballot: mismatching ballot encryption {ballot.object_id}",
        )

    return Verification(True, message=None)


def verify_decryption(
    tally: PlaintextTally,
    election_public_keys: Dict[GuardianId, ElectionPublicKey],
    context: CiphertextElectionContext,
) -> Verification:
    for _, contest in tally.contests.items():
        for selection_id, selection in contest.selections.items():
            for share in selection.shares:
                election_public_key = election_public_keys.get(share.guardian_id).key
                if not share.proof.is_valid(
                    selection.message,
                    election_public_key,
                    share.share,
                    context.crypto_extended_base_hash,
                ):
                    return Verification(
                        False,
                        message=f"verify_decryption: {selection_id} selection is not valid",
                    )

    return Verification(True, message=None)


def verify_aggregation(
    submitted_ballots: List[SubmittedBallot],
    tally: CiphertextTally,
    manifest: Manifest,
    context: CiphertextElectionContext,
) -> Verification:
    new_tally = CiphertextTally("verify", InternalManifest(manifest), context)

    for ballot in submitted_ballots:
        new_tally.append(ballot, True)

    if (
        isinstance(tally, CiphertextTally)
        and new_tally.cast_ballot_ids == tally.cast_ballot_ids
        and new_tally.spoiled_ballot_ids == tally.spoiled_ballot_ids
        and new_tally.contests == tally.contests
    ):
        return Verification(True, message=None)

    return Verification(
        False,
        message="verify_aggregation: aggregated value of ballots doesn't matches with tally",
    )
