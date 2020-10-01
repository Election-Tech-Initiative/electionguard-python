from typing import Dict, List, Optional

from .auxiliary import AuxiliaryDecrypt
from .ballot import (
    CiphertextAcceptedBallot,
    CiphertextSelection,
)
from .data_store import DataStore
from .decryption_share import (
    BallotDecryptionShare,
    CompensatedBallotDecryptionShare,
    CiphertextDecryptionSelection,
    CiphertextCompensatedDecryptionSelection,
    CiphertextDecryptionContest,
    CiphertextCompensatedDecryptionContest,
    TallyDecryptionShare,
    CompensatedTallyDecryptionShare,
    create_ciphertext_decryption_selection,
)
from .election import CiphertextElectionContext
from .election_polynomial import compute_lagrange_coefficient
from .group import ElementModP, ElementModQ, mult_p, pow_p
from .guardian import Guardian, PublicKeySet
from .key_ceremony import ElectionPublicKey
from .logs import log_warning
from .rsa import rsa_decrypt
from .scheduler import Scheduler
from .tally import (
    CiphertextTally,
    CiphertextTallyContest,
)

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
) -> Optional[TallyDecryptionShare]:
    """
    Compute a decryptions share for a guardian

    :param guardian: The guardian who will partially decrypt the tally
    :param tally: The election tally to decrypt
    :context: The public election encryption context
    :return: a `TallyDecryptionShare` or `None` if there is an error
    """

    if not scheduler:
        scheduler = Scheduler()

    contests = compute_decryption_share_for_cast_contests(
        guardian, tally, context, scheduler
    )
    if contests is None:
        return None

    spoiled_ballots = compute_decryption_share_for_spoiled_ballots(
        guardian, tally, context, scheduler
    )

    if spoiled_ballots is None:
        return None

    return TallyDecryptionShare(
        guardian.object_id,
        guardian.share_election_public_key().key,
        contests,
        spoiled_ballots,
    )


def compute_compensated_decryption_share(
    guardian: Guardian,
    missing_guardian_id: str,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedTallyDecryptionShare]:
    """
    Compute a compensated decryptions share for a guardian

    :param guardian: The guardian who will partially decrypt the tally
    :param missing_guardian_id: the missing guardian id to compensate
    :param tally: The election tally to decrypt
    :context: The public election encryption context
    :return: a `TallyDecryptionShare` or `None` if there is an error
    """
    if not scheduler:
        scheduler = Scheduler()

    contests = compute_compensated_decryption_share_for_cast_contests(
        guardian, missing_guardian_id, tally, context, decrypt, scheduler
    )
    if contests is None:
        return None

    spoiled_ballots = compute_compensated_decryption_share_for_spoiled_ballots(
        guardian, missing_guardian_id, tally, context, decrypt, scheduler
    )

    if spoiled_ballots is None:
        return None

    return CompensatedTallyDecryptionShare(
        guardian.object_id,
        missing_guardian_id,
        guardian.share_election_public_key().key,
        contests,
        spoiled_ballots,
    )


def compute_decryption_share_for_cast_contests(
    guardian: Guardian,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[CONTEST_ID, CiphertextDecryptionContest]]:
    """
    Compute the decryption for all of the cast contests in the Ciphertext Tally
    """
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
    if not scheduler:
        scheduler = Scheduler()

    for contest in tally.cast.values():
        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        selection_decryptions: List[
            Optional[CiphertextDecryptionSelection]
        ] = scheduler.schedule(
            compute_decryption_share_for_selection,
            [
                (guardian, selection, context)
                for (_, selection) in contest.tally_selections.items()
            ],
            with_shared_resources=True,
        )

        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute share for guardian {guardian.object_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextDecryptionContest(
            contest.object_id, guardian.object_id, contest.description_hash, selections
        )

    return contests


def compute_compensated_decryption_share_for_cast_contests(
    guardian: Guardian,
    missing_guardian_id: str,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest]]:
    """
    Compute the compensated decryption for all of the cast contests in the Ciphertext Tally
    """
    if not scheduler:
        scheduler = Scheduler()
    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in tally.cast.values():
        selections: Dict[SELECTION_ID, CiphertextCompensatedDecryptionSelection] = {}
        selection_decryptions: List[
            Optional[CiphertextCompensatedDecryptionSelection]
        ] = scheduler.schedule(
            compute_compensated_decryption_share_for_selection,
            [
                (guardian, missing_guardian_id, selection, context, decrypt)
                for (_, selection) in contest.tally_selections.items()
            ],
            with_shared_resources=True,
        )

        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute share for guardian {guardian.object_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextCompensatedDecryptionContest(
            contest.object_id,
            guardian.object_id,
            missing_guardian_id,
            contest.description_hash,
            selections,
        )
    return contests


def compute_decryption_share_for_spoiled_ballots(
    guardian: Guardian,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[BALLOT_ID, BallotDecryptionShare]]:
    """
    Compute the decryption for all spoiled ballots in the Ciphertext Tally
    """
    spoiled_ballots: Dict[BALLOT_ID, BallotDecryptionShare] = {}
    if not scheduler:
        scheduler = Scheduler()

    for spoiled_ballot in tally.spoiled_ballots.values():
        computed_share = compute_decryption_share_for_ballot(
            guardian, spoiled_ballot, context, scheduler
        )

        if computed_share:
            spoiled_ballots[spoiled_ballot.object_id] = computed_share
        else:
            return None

    return spoiled_ballots


def compute_decryption_share_for_ballot(
    guardian: Guardian,
    ballot: CiphertextAcceptedBallot,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[BallotDecryptionShare]:
    """
    Compute the decryption for a single ballot
    """
    if not scheduler:
        scheduler = Scheduler()

    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
    for contest in ballot.contests:
        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        selection_decryptions: List[
            Optional[CiphertextDecryptionSelection]
        ] = scheduler.schedule(
            compute_decryption_share_for_selection,
            [(guardian, selection, context) for selection in contest.ballot_selections],
            with_shared_resources=True,
        )
        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute spoiled ballot share for guardian {guardian.object_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextDecryptionContest(
            contest.object_id, guardian.object_id, contest.description_hash, selections,
        )
    return BallotDecryptionShare(
        guardian.object_id,
        guardian.share_election_public_key().key,
        ballot.object_id,
        contests,
    )


def compute_compensated_decryption_share_for_spoiled_ballots(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[Dict[BALLOT_ID, CompensatedBallotDecryptionShare]]:
    """
    Compute the decryption for all spoiled ballots in the Ciphertext Tally
    """
    spoiled_ballots: Dict[BALLOT_ID, CompensatedBallotDecryptionShare] = {}
    if not scheduler:
        scheduler = Scheduler()

    for spoiled_ballot in tally.spoiled_ballots.values():
        compensated_ballot = compute_compensated_decryption_share_for_ballot(
            guardian, missing_guardian_id, spoiled_ballot, context, decrypt, scheduler
        )

        if compensated_ballot:
            spoiled_ballots[spoiled_ballot.object_id] = compensated_ballot
        else:
            return None
    return spoiled_ballots


def compute_compensated_decryption_share_for_ballot(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    ballot: CiphertextAcceptedBallot,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedBallotDecryptionShare]:
    """
    Compute the decryption for a single ballot
    """
    if not scheduler:
        scheduler = Scheduler()

    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}
    for contest in ballot.contests:
        selections: Dict[SELECTION_ID, CiphertextCompensatedDecryptionSelection] = {}
        selection_decryptions: List[
            Optional[CiphertextCompensatedDecryptionSelection]
        ] = scheduler.schedule(
            compute_compensated_decryption_share_for_selection,
            [
                (guardian, missing_guardian_id, selection, context, decrypt)
                for selection in contest.ballot_selections
            ],
            with_shared_resources=True,
        )
        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute compensated spoiled ballot share for guardian {guardian.object_id} missing: {missing_guardian_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextCompensatedDecryptionContest(
            contest.object_id,
            guardian.object_id,
            missing_guardian_id,
            contest.description_hash,
            selections,
        )
    return CompensatedBallotDecryptionShare(
        guardian.object_id,
        missing_guardian_id,
        guardian.share_election_public_key().key,
        ballot.object_id,
        contests,
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
            selection.description_hash,
            decryption,
            proof,
        )
    else:
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
            f"compute compensated decryption share failed for {available_guardian.object_id} missing: {missing_guardian_id} {selection.object_id}"
        )
        return None

    (decryption, proof) = compensated

    recovery_public_key = available_guardian.recovery_public_key_for(
        missing_guardian_id
    )

    if recovery_public_key is None:
        log_warning(
            f"compute compensated decryption share failed for {available_guardian.object_id} missing recovery key: {missing_guardian_id} {selection.object_id}"
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
            selection.description_hash,
            decryption,
            recovery_public_key,
            proof,
        )
        return share
    else:
        log_warning(
            f"compute compensated decryption share proof failed for {available_guardian.object_id} missing: {missing_guardian_id} {selection.object_id}"
        )
        return None


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
        guardian_keys.sequence_order, *other_guardian_orders,
    )


def compute_lagrange_coefficients_for_guardians(
    all_available_guardian_keys: List[PublicKeySet],
) -> Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]:
    """
    Produce all Lagrange coefficients for a collection of available Guardians, to be used when reconstructing a missing share.
    """
    return {
        guardian_keys.owner_id: compute_lagrange_coefficients_for_guardian(
            all_available_guardian_keys, guardian_keys
        )
        for guardian_keys in all_available_guardian_keys
    }


def reconstruct_missing_tally_decryption_shares(
    ciphertext_tally: CiphertextTally,
    missing_guardians: DataStore[MISSING_GUARDIAN_ID, ElectionPublicKey],
    compensated_shares: Dict[
        MISSING_GUARDIAN_ID,
        Dict[AVAILABLE_GUARDIAN_ID, CompensatedTallyDecryptionShare],
    ],
    lagrange_coefficients: Dict[
        MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]
    ],
) -> Optional[Dict[MISSING_GUARDIAN_ID, TallyDecryptionShare]]:
    """
    Use all available guardians to reconstruct the missing shares for all missing guardians
    """

    reconstructed_shares: Dict[MISSING_GUARDIAN_ID, TallyDecryptionShare] = {}
    for missing_guardian_id, shares in compensated_shares.items():

        # Make sure there is a public key
        public_key = missing_guardians.get(missing_guardian_id)
        if public_key is None:
            log_warning(
                f"Could not reconstruct tally for {missing_guardian_id} with no public key"
            )
            return None

        # make sure there are computed lagrange coefficients:
        lagrange_coefficients_for_missing: Dict[
            AVAILABLE_GUARDIAN_ID, ElementModQ
        ] = lagrange_coefficients.get(missing_guardian_id, {})
        if not any(lagrange_coefficients):
            log_warning(
                f"Could not reconstruct tally for {missing_guardian_id} with no lagrange coefficients"
            )
            return None

        # iterate through the tallies and accumulate
        # all of the shares for this guardian
        contests = reconstruct_decryption_contests(
            missing_guardian_id,
            ciphertext_tally.cast,
            shares,
            lagrange_coefficients_for_missing,
        )

        # iterate through the spoiled ballots and accumulate
        # all of the shares for this guardian
        spoiled_ballots = reconstruct_decryption_ballots(
            missing_guardian_id,
            public_key,
            ciphertext_tally.spoiled_ballots,
            shares,
            lagrange_coefficients_for_missing,
        )

        reconstructed_shares[missing_guardian_id] = TallyDecryptionShare(
            missing_guardian_id, public_key.key, contests, spoiled_ballots
        )

    return reconstructed_shares


def reconstruct_decryption_contests(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    cast_tally: Dict[CONTEST_ID, CiphertextTallyContest],
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedTallyDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> Dict[CONTEST_ID, CiphertextDecryptionContest]:
    """
    Recontruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param cast_tally: The collection of `CiphertextTallyContest` that is cast
    :shares: the collection of `CompensatedTallyDecryptionShare` for the missing guardian
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    # iterate through the tallies and accumulate all of the shares for this guardian
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
    for contest_id, tally_contest in cast_tally.items():
        contest_shares: Dict[
            AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionContest
        ] = {
            available_guardian_id: compensated_share.contests[tally_contest.object_id]
            for available_guardian_id, compensated_share in shares.items()
        }

        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        for (selection_id, tally_selection,) in tally_contest.tally_selections.items():

            # collect all of the shares generated for each selection
            compensated_selection_shares: Dict[
                AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
            ] = {
                available_guardian_id: compensated_contest.selections[selection_id]
                for available_guardian_id, compensated_contest in contest_shares.items()
            }

            share_pow_p = []
            for available_guardian_id, share in compensated_selection_shares.items():
                share_pow_p.append(
                    pow_p(share.share, lagrange_coefficients[available_guardian_id])
                )

            reconstructed_share = mult_p(*share_pow_p)

            selections[selection_id] = create_ciphertext_decryption_selection(
                selection_id,
                missing_guardian_id,
                tally_selection.description_hash,
                reconstructed_share,
                compensated_selection_shares,
            )
        contests[contest_id] = CiphertextDecryptionContest(
            contest_id, missing_guardian_id, tally_contest.description_hash, selections,
        )

    return contests


def reconstruct_decryption_ballots(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedTallyDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> Dict[BALLOT_ID, BallotDecryptionShare]:
    """
    Recontruct the missing Decryption shares for a missing guardian from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: the public key for the missing guardian
    :param spoiled_ballots: The collection of `CiphertextAcceptedBallot` that is spoiled
    :shares: the collection of `CompensatedTallyDecryptionShare` for the missing guardian
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    spoiled_ballot_shares: Dict[BALLOT_ID, BallotDecryptionShare] = {}
    for ballot_id, spoiled_ballot in spoiled_ballots.items():
        # iterate through the tallies and accumulate all of the shares for this guardian
        shares_for_ballot: Dict[GUARDIAN_ID, CompensatedBallotDecryptionShare] = {
            available_guardian_id: compensated_ballot
            for available_guardian_id, compensated_share in shares.items()
            for compensated_ballot_id, compensated_ballot in compensated_share.spoiled_ballots.items()
            if compensated_ballot_id == ballot_id
        }
        ballot_share = reconstruct_decryption_ballot(
            missing_guardian_id,
            public_key,
            spoiled_ballot,
            shares_for_ballot,
            lagrange_coefficients,
        )

        spoiled_ballot_shares[spoiled_ballot.object_id] = ballot_share
    return spoiled_ballot_shares


def reconstruct_decryption_ballot(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    ballot: CiphertextAcceptedBallot,
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedBallotDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> BallotDecryptionShare:
    """
    Reconstruct a missing ballot Decryption share for a missing guardian from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: the public key for the missing guardian
    :param ballots: The `CiphertextAcceptedBallot` to reconstruct
    :shares: the collection of `CompensatedBallotDecryptionShare` for the missing guardian, each keyed by the ID of the guardian that produced it
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
    for contest in ballot.contests:
        contest_shares: Dict[
            AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionContest
        ] = {
            available_guardian_id: compensated_ballot.contests[contest.object_id]
            for available_guardian_id, compensated_ballot in shares.items()
        }

        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        for selection in contest.ballot_selections:

            # collect all of the shares generated for each selection
            compensated_selection_shares: Dict[
                AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
            ] = {
                available_guardian_id: compensated_contest.selections[
                    selection.object_id
                ]
                for available_guardian_id, compensated_contest in contest_shares.items()
            }

            # compute the reconstructed share
            reconstructed_share = mult_p(
                *[
                    pow_p(share.share, lagrange_coefficients[available_guardian_id])
                    for available_guardian_id, share in compensated_selection_shares.items()
                ]
            )
            selections[selection.object_id] = create_ciphertext_decryption_selection(
                selection.object_id,
                missing_guardian_id,
                selection.description_hash,
                reconstructed_share,
                compensated_selection_shares,
            )
        contests[contest.object_id] = CiphertextDecryptionContest(
            contest.object_id,
            missing_guardian_id,
            contest.description_hash,
            selections,
        )
    return BallotDecryptionShare(
        missing_guardian_id, public_key.key, ballot.object_id, contests,
    )
