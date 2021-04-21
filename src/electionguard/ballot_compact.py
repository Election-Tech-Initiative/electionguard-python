from dataclasses import dataclass
from typing import Dict, List


from .ballot import (
    SubmittedBallot,
    ExtendedData,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    create_ballot_hash,
)
from .ballot_box import BallotBoxState
from .election import CiphertextElectionContext
from .encrypt import encrypt_ballot_contests
from .group import ElementModQ
from .manifest import (
    ContestDescriptionWithPlaceholders,
    InternalManifest,
)
from .utils import get_optional

YES_VOTE = 1
NO_VOTE = 0


@dataclass
class CompactPlaintextBallot:
    """A compact plaintext representation of ballot minimized for data size"""

    object_id: str
    style_id: str
    selections: List[bool]
    extended_data: Dict[int, ExtendedData]


@dataclass
class CompactSubmittedBallot:
    """A compact submitted ballot minimized for data size"""

    compact_plaintext_ballot: CompactPlaintextBallot
    timestamp: int
    ballot_nonce: ElementModQ
    code_seed: ElementModQ
    code: ElementModQ
    ballot_box_state: BallotBoxState


def compress_plaintext_ballot(ballot: PlaintextBallot) -> CompactPlaintextBallot:
    """Compress a plaintext ballot into a compact plaintext ballot"""
    selections = _get_compact_selections(ballot)
    extended_data = _get_compact_extended_data(ballot)

    return CompactPlaintextBallot(
        ballot.object_id, ballot.style_id, selections, extended_data
    )


def compress_submitted_ballot(
    ballot: SubmittedBallot,
    plaintext_ballot: PlaintextBallot,
    ballot_nonce: ElementModQ,
) -> CompactSubmittedBallot:
    """Compress a submitted ballot into a compact submitted ballot"""
    return CompactSubmittedBallot(
        compress_plaintext_ballot(plaintext_ballot),
        ballot.timestamp,
        ballot_nonce,
        ballot.code_seed,
        ballot.code,
        ballot.state,
    )


def expand_compact_submitted_ballot(
    compact_ballot: CompactSubmittedBallot,
    internal_manifest: InternalManifest,
    context: CiphertextElectionContext,
) -> SubmittedBallot:
    """
    Expand a compact submitted ballot using context and
    the election manifest into a submitted ballot
    """
    # Expand ballot and encrypt & hash contests
    plaintext_ballot = expand_compact_plaintext_ballot(
        compact_ballot.compact_plaintext_ballot, internal_manifest
    )
    contests = get_optional(
        encrypt_ballot_contests(
            plaintext_ballot, internal_manifest, context, compact_ballot.ballot_nonce
        )
    )
    crypto_hash = create_ballot_hash(
        plaintext_ballot.object_id, internal_manifest.manifest_hash, contests
    )

    return SubmittedBallot(
        plaintext_ballot.object_id,
        plaintext_ballot.style_id,
        internal_manifest.manifest_hash,
        compact_ballot.code_seed,
        contests,
        compact_ballot.code,
        compact_ballot.timestamp,
        crypto_hash,
        compact_ballot.ballot_nonce,
        compact_ballot.ballot_box_state,
    )


def expand_compact_plaintext_ballot(
    compact_ballot: CompactPlaintextBallot, internal_manifest: InternalManifest
) -> PlaintextBallot:
    """Expand a compact plaintext ballot into the original plaintext ballot"""
    return PlaintextBallot(
        compact_ballot.object_id,
        compact_ballot.style_id,
        _get_plaintext_contests(compact_ballot, internal_manifest),
    )


def _get_compact_selections(ballot: PlaintextBallot) -> List[bool]:
    selections = []
    for contest in ballot.contests:
        for selection in contest.ballot_selections:
            selections.append(selection.vote == YES_VOTE)
    return selections


def _get_compact_extended_data(ballot: PlaintextBallot) -> Dict[int, ExtendedData]:
    extended_data = {}
    index = 0
    for contest in ballot.contests:
        for selection in contest.ballot_selections:
            index += 1
            if selection.extended_data:
                extended_data[index] = selection.extended_data
    return extended_data


def _get_plaintext_contests(
    compact_ballot: CompactPlaintextBallot, internal_manifest: InternalManifest
) -> List[PlaintextBallotContest]:
    """Get ballot contests from compact plaintext ballot"""
    index = 0
    ballot_style_contests = _get_ballot_style_contests(
        compact_ballot.style_id, internal_manifest
    )

    contests: List[PlaintextBallotContest] = []
    for manifest_contest in sorted(
        internal_manifest.contests, key=lambda c: c.sequence_order
    ):
        contest_in_style = (
            ballot_style_contests.get(manifest_contest.object_id) is not None
        )

        # Iterate through selections. If contest not in style, mark placeholder
        selections: List[PlaintextBallotSelection] = []
        for selection in sorted(
            manifest_contest.ballot_selections, key=lambda s: s.sequence_order
        ):
            selections.append(
                PlaintextBallotSelection(
                    selection.object_id,
                    YES_VOTE if compact_ballot.selections[index] else NO_VOTE,
                    not contest_in_style,
                    compact_ballot.extended_data.get(index),
                )
            )
            index += 1

        contests.append(PlaintextBallotContest(manifest_contest.object_id, selections))
    return contests


def _get_ballot_style_contests(
    ballot_style_id: str, internal_manifest: InternalManifest
) -> Dict[str, ContestDescriptionWithPlaceholders]:
    ballot_style_contests = internal_manifest.get_contests_for(ballot_style_id)
    return {contest.object_id: contest for contest in ballot_style_contests}
