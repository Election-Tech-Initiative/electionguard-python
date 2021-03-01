from typing import Dict, List, Optional

from .auxiliary import AuxiliaryDecrypt
from .ballot import (
    CiphertextAcceptedBallot,
    CiphertextSelection,
    CiphertextContest,
)
from .decryption_share import (
    CiphertextDecryptionSelection,
    CiphertextCompensatedDecryptionSelection,
    CiphertextDecryptionContest,
    CiphertextCompensatedDecryptionContest,
    create_ciphertext_decryption_selection,
    DecryptionShare,
    CompensatedDecryptionShare,
)
from .election import CiphertextElectionContext
from .election_polynomial import compute_lagrange_coefficient
from .group import ElementModP, ElementModQ, mult_p, pow_p
from .guardian import Guardian, PublicKeySet
from .key_ceremony import ElectionPublicKey
from .logs import log_warning
from .rsa import rsa_decrypt
from .scheduler import Scheduler
from .tally import CiphertextTally

from .types import BALLOT_ID, CONTEST_ID, GUARDIAN_ID, SELECTION_ID

AVAILABLE_GUARDIAN_ID = GUARDIAN_ID
MISSING_GUARDIAN_ID = GUARDIAN_ID

GUARDIAN_PUBLIC_KEY = ElementModP
ELECTION_PUBLIC_KEY = ElementModP


def compute_decryption_share(
    guardian: Guardian,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[DecryptionShare]:
    """
    Compute the decryption for all of the cast contests in the Ciphertext Tally
    """

    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_decryption_share_for_contest(
            guardian,
            CiphertextContest(
                contest.object_id,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            context,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return DecryptionShare(
        tally.object_id,
        guardian.object_id,
        guardian.share_election_public_key().key,
        contests,
    )


def compute_compensated_decryption_share(
    guardian: Guardian,
    missing_guardian_id: str,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for all of the cast contests in the Ciphertext Tally
    """

    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_compensated_decryption_share_for_contest(
            guardian,
            missing_guardian_id,
            CiphertextContest(
                contest.object_id,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            context,
            decrypt,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return CompensatedDecryptionShare(
        tally.object_id,
        guardian.object_id,
        missing_guardian_id,
        guardian.share_election_public_key().key,
        contests,
    )


def compute_decryption_share_for_ballots(
    guardian: Guardian,
    ballots: List[CiphertextAcceptedBallot],
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[BALLOT_ID, DecryptionShare]]:
    """
    Compute the decryption for a list of ballots for a guardian
    """
    shares: Dict[BALLOT_ID, DecryptionShare] = {}

    for ballot in ballots:
        ballot_share = compute_decryption_share_for_ballot(
            guardian, ballot, context, scheduler
        )
        if ballot_share is None:
            return None
        shares[ballot.object_id] = ballot_share

    return shares


def compute_compensated_decryption_share_for_ballots(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    ballots: List[CiphertextAcceptedBallot],
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[BALLOT_ID, CompensatedDecryptionShare]]:
    """
    Compute the compensated decryption for ballots for a guardian
    """
    shares: Dict[BALLOT_ID, CompensatedDecryptionShare] = {}

    for ballot in ballots:
        ballot_share = compute_compensated_decryption_share_for_ballot(
            guardian, missing_guardian_id, ballot, context, decrypt, scheduler
        )
        if ballot_share is None:
            return None
        shares[ballot.object_id] = ballot_share

    return shares


def compute_decryption_share_for_ballot(
    guardian: Guardian,
    ballot: CiphertextAcceptedBallot,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[DecryptionShare]:
    """
    Compute the decryption for a single ballot
    """
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_decryption_share_for_contest(
            guardian,
            CiphertextContest(
                contest.object_id, contest.description_hash, contest.ballot_selections
            ),
            context,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return DecryptionShare(
        ballot.object_id,
        guardian.object_id,
        guardian.share_election_public_key().key,
        contests,
    )


def compute_compensated_decryption_share_for_ballot(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    ballot: CiphertextAcceptedBallot,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for a single ballot
    """
    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_compensated_decryption_share_for_contest(
            guardian,
            missing_guardian_id,
            CiphertextContest(
                contest.object_id, contest.description_hash, contest.ballot_selections
            ),
            context,
            decrypt,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return CompensatedDecryptionShare(
        ballot.object_id,
        guardian.object_id,
        missing_guardian_id,
        guardian.share_election_public_key().key,
        contests,
    )


def compute_decryption_share_for_contest(
    guardian: Guardian,
    contest: CiphertextContest,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CiphertextDecryptionContest]:
    if not scheduler:
        scheduler = Scheduler()

    selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}

    decryptions: List[Optional[CiphertextDecryptionSelection]] = scheduler.schedule(
        compute_decryption_share_for_selection,
        [(guardian, selection, context) for selection in contest.selections],
        with_shared_resources=True,
    )

    for decryption in decryptions:
        if decryption is None:
            return None
        selections[decryption.object_id] = decryption

    return CiphertextDecryptionContest(
        contest.object_id,
        guardian.object_id,
        contest.description_hash,
        selections,
    )


def compute_compensated_decryption_share_for_contest(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    contest: CiphertextContest,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CiphertextCompensatedDecryptionContest]:
    if not scheduler:
        scheduler = Scheduler()

    selections: Dict[SELECTION_ID, CiphertextCompensatedDecryptionSelection] = {}

    selection_decryptions: List[
        Optional[CiphertextCompensatedDecryptionSelection]
    ] = scheduler.schedule(
        compute_compensated_decryption_share_for_selection,
        [
            (guardian, missing_guardian_id, selection, context, decrypt)
            for selection in contest.selections
        ],
        with_shared_resources=True,
    )

    for decryption in selection_decryptions:
        if decryption is None:
            return None
        selections[decryption.object_id] = decryption

    return CiphertextCompensatedDecryptionContest(
        contest.object_id,
        guardian.object_id,
        missing_guardian_id,
        contest.description_hash,
        selections,
    )


def compute_decryption_share_for_selection(
    guardian: Guardian,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
) -> Optional[CiphertextDecryptionSelection]:
    """
    Compute a partial decryption for a specific selection

    :param guardian: The guardian who will partially decrypt the selection
    :param selection: The specific selection to decrypt
    :context: The public election encryption context
    :return: a `CiphertextDecryptionSelection` or `None` if there is an error
    """

    (decryption, proof) = guardian.partially_decrypt(
        selection.ciphertext, context.crypto_extended_base_hash
    )

    if proof.is_valid(
        selection.ciphertext,
        guardian.share_election_public_key().key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        return create_ciphertext_decryption_selection(
            selection.object_id,
            guardian.object_id,
            decryption,
            proof,
        )
    log_warning(
        f"compute decryption share proof failed for {guardian.object_id} {selection.object_id} with invalid proof"
    )
    return None


def compute_compensated_decryption_share_for_selection(
    available_guardian: Guardian,
    missing_guardian_id: str,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
) -> Optional[CiphertextCompensatedDecryptionSelection]:
    """
    Compute a compensated decryption share for a specific selection using the
    avialable guardian's share of the missing guardian's private key polynomial

    :param available_guardian: The available guardian that will partially decrypt the selection
    :param missing_guardian_id: The id of the guardian that is missing
    :param selection: The specific selection to decrypt
    :context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionSelection` or `None` if there is an error
    """

    compensated = available_guardian.compensate_decrypt(
        missing_guardian_id,
        selection.ciphertext,
        context.crypto_extended_base_hash,
        decrypt=decrypt,
    )

    if compensated is None:
        log_warning(
            (
                f"compute compensated decryption share failed for {available_guardian.object_id} "
                f"missing: {missing_guardian_id} {selection.object_id}"
            )
        )
        return None

    (decryption, proof) = compensated

    recovery_public_key = available_guardian.recovery_public_key_for(
        missing_guardian_id
    )

    if recovery_public_key is None:
        log_warning(
            (
                f"compute compensated decryption share failed for {available_guardian.object_id} "
                f"missing recovery key: {missing_guardian_id} {selection.object_id}"
            )
        )
        return None

    if proof.is_valid(
        selection.ciphertext,
        recovery_public_key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        share = CiphertextCompensatedDecryptionSelection(
            selection.object_id,
            available_guardian.object_id,
            missing_guardian_id,
            decryption,
            recovery_public_key,
            proof,
        )
        return share
    log_warning(
        (
            f"compute compensated decryption share proof failed for {available_guardian.object_id} "
            f"missing: {missing_guardian_id} {selection.object_id}"
        )
    )
    return None


def reconstruct_decryption_share(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    tally: CiphertextTally,
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> DecryptionShare:
    """
    Recontruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param cast_tally: The collection of `CiphertextTallyContest` that is cast
    :shares: the collection of `CompensatedTallyDecryptionShare` for the missing guardian
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_id,
            CiphertextContest(
                contest.object_id,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            shares,
            lagrange_coefficients,
        )

    return DecryptionShare(
        tally.object_id, missing_guardian_id, public_key.key, contests
    )


def reconstruct_decryption_shares_for_ballots(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
    shares: Dict[BALLOT_ID, Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> Dict[BALLOT_ID, DecryptionShare]:
    """
    Recontruct the missing Decryption shares for a missing guardian from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: the public key for the missing guardian
    :param ballots: The collection of `CiphertextAcceptedBallot` that is spoiled
    :shares: the collection of `CompensatedDecryptionShare` for the missing guardian
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    ballot_shares: Dict[BALLOT_ID, DecryptionShare] = {}

    for ballot_id, ballot in ballots.items():
        ballot_share = reconstruct_decryption_share_for_ballot(
            missing_guardian_id,
            public_key,
            ballot,
            shares[ballot_id],
            lagrange_coefficients,
        )
        ballot_shares[ballot.object_id] = ballot_share

    return ballot_shares


def reconstruct_decryption_share_for_ballot(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    ballot: CiphertextAcceptedBallot,
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> DecryptionShare:
    """
    Reconstruct a missing ballot Decryption share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: the public key for the missing guardian
    :param ballots: The `CiphertextAcceptedBallot` to reconstruct
    :shares: the collection of `CompensatedBallotDecryptionShare` for
        the missing guardian, each keyed by the ID of the guardian that produced it
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_id,
            CiphertextContest(
                contest.object_id, contest.description_hash, contest.ballot_selections
            ),
            shares,
            lagrange_coefficients,
        )

    return DecryptionShare(
        ballot.object_id,
        missing_guardian_id,
        public_key.key,
        contests,
    )


def reconstruct_decryption_contest(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    contest: CiphertextContest,
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> CiphertextDecryptionContest:
    """
    Recontruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param cast_tally: The collection of `CiphertextTallyContest` that is cast
    :shares: the collection of `CompensatedTallyDecryptionShare` for the missing guardian
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """

    contest_shares: Dict[
        AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionContest
    ] = {
        available_guardian_id: compensated_share.contests[contest.object_id]
        for available_guardian_id, compensated_share in shares.items()
    }

    selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
    for selection in contest.selections:

        # collect all of the shares generated for each selection
        compensated_selection_shares: Dict[
            AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
        ] = {
            available_guardian_id: compensated_contest.selections[selection.object_id]
            for available_guardian_id, compensated_contest in contest_shares.items()
        }

        share_pow_p = []
        for available_guardian_id, share in compensated_selection_shares.items():
            share_pow_p.append(
                pow_p(share.share, lagrange_coefficients[available_guardian_id])
            )

        reconstructed_share = mult_p(*share_pow_p)

        selections[selection.object_id] = create_ciphertext_decryption_selection(
            selection.object_id,
            missing_guardian_id,
            reconstructed_share,
            compensated_selection_shares,
        )
    return CiphertextDecryptionContest(
        contest.object_id,
        missing_guardian_id,
        contest.description_hash,
        selections,
    )


def compute_lagrange_coefficients_for_guardians(
    all_available_guardian_keys: List[PublicKeySet],
) -> Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]:
    """
    Produce all Lagrange coefficients for a collection of available
    Guardians, to be used when reconstructing a missing share.
    """
    return {
        guardian_keys.owner_id: compute_lagrange_coefficients_for_guardian(
            all_available_guardian_keys, guardian_keys
        )
        for guardian_keys in all_available_guardian_keys
    }


def compute_lagrange_coefficients_for_guardian(
    all_available_guardian_keys: List[PublicKeySet], guardian_keys: PublicKeySet
) -> ElementModQ:
    """
    Produce a Lagrange coefficient for a single Guardian, to be used when reconstructing a missing share.
    """
    other_guardian_orders = [
        g.sequence_order
        for g in all_available_guardian_keys
        if g.owner_id != guardian_keys.owner_id
    ]
    return compute_lagrange_coefficient(
        guardian_keys.sequence_order,
        *other_guardian_orders,
    )
