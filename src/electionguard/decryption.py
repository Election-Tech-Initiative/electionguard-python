from typing import Dict, List, Optional, Tuple
from electionguard.chaum_pedersen import ChaumPedersenProof, make_chaum_pedersen

from electionguard.elgamal import ElGamalCiphertext
from electionguard.utils import get_optional

from .ballot import (
    SubmittedBallot,
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
from .group import (
    ElementModP,
    ElementModQ,
    ONE_MOD_P,
    mult_p,
    pow_p,
    pow_q,
    rand_q,
)
from .key_ceremony import (
    CoordinateData,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPublicKey,
    get_backup_seed,
)
from .logs import log_warning
from .scheduler import Scheduler
from .tally import CiphertextTally

from .type import ContestId, GuardianId, SelectionId

RecoveryPublicKey = ElementModP


def compute_decryption_share(
    key_pair: ElectionKeyPair,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[DecryptionShare]:
    """
    Compute the decryption for all of the contests in the Ciphertext Tally

    :param guardian_keys: Guardian's election key pair
    :param tally: Encrypted tally to get decryption share of
    :param context: Election context
    :param scheduler: Scheduler
    :return: Return a guardian's decryption share of tally or None if error
    """

    contests: Dict[ContestId, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_decryption_share_for_contest(
            key_pair,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
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
        key_pair.owner_id,
        key_pair.key_pair.public_key,
        contests,
    )


def compute_compensated_decryption_share(
    missing_guardian_coordinate: ElementModQ,
    present_guardian_key: ElectionPublicKey,
    missing_guardian_key: ElectionPublicKey,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for all of the contests in the Ciphertext Tally

    :param guardian_key: Guardian's election public key
    :param missing_guardian_key: Missing guardian's election public key
    :param missing_guardian_backup: Missing guardian's election partial key backup
    :param tally: Encrypted tally to get decryption share of
    :param context: Election context
    :param scheduler: Scheduler
    :return: Return a guardian's compensated decryption share of tally for the missing guardian
        or None if error
    """

    contests: Dict[ContestId, CiphertextCompensatedDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_compensated_decryption_share_for_contest(
            missing_guardian_coordinate,
            present_guardian_key,
            missing_guardian_key,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            context,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return CompensatedDecryptionShare(
        tally.object_id,
        present_guardian_key.owner_id,
        missing_guardian_key.owner_id,
        present_guardian_key.key,
        contests,
    )


def compute_decryption_share_for_ballot(
    key_pair: ElectionKeyPair,
    ballot: SubmittedBallot,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[DecryptionShare]:
    """
    Compute the decryption for a single ballot

    :param guardian_keys: Guardian's election key pair
    :param ballot: Ballot to be decrypted
    :param context: The public election encryption context
    :param scheduler: Scheduler
    :return: Decryption share for ballot or `None` if there is an error
    """
    contests: Dict[ContestId, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_decryption_share_for_contest(
            key_pair,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                contest.ballot_selections,
            ),
            context,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return DecryptionShare(
        ballot.object_id,
        key_pair.owner_id,
        key_pair.share().key,
        contests,
    )


def compute_compensated_decryption_share_for_ballot(
    missing_guardian_coordinate: ElementModQ,
    missing_guardian_key: ElectionPublicKey,
    present_guardian_key: ElectionPublicKey,
    ballot: SubmittedBallot,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for a single ballot

    :param missing_guardian_coordinate: Missing guardian's election partial key backup
    :param missing_guardian_key: Missing guardian's election public key
    :param present_guardian_key: Present guardian's election public key
    :param ballot: Encrypted ballot to get decryption share of
    :param context: Election context
    :param scheduler: Scheduler
    :return: Return a guardian's compensated decryption share of ballot for the missing guardian
        or None if error
    """
    contests: Dict[ContestId, CiphertextCompensatedDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_compensated_decryption_share_for_contest(
            missing_guardian_coordinate,
            present_guardian_key,
            missing_guardian_key,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                contest.ballot_selections,
            ),
            context,
            scheduler,
        )
        if contest_share is None:
            return None
        contests[contest.object_id] = contest_share

    return CompensatedDecryptionShare(
        ballot.object_id,
        present_guardian_key.owner_id,
        missing_guardian_key.owner_id,
        present_guardian_key.key,
        contests,
    )


def compute_decryption_share_for_contest(
    key_pair: ElectionKeyPair,
    contest: CiphertextContest,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CiphertextDecryptionContest]:
    """
    Compute the decryption share for a single contest

    :param guardian_keys: Guardian's election key pair
    :param contest: Contest to be decrypted
    :param context: The public election encryption context
    :param scheduler: Scheduler
    :return: Decryption share for contest or `None` if there is an error
    """
    if not scheduler:
        scheduler = Scheduler()

    selections: Dict[SelectionId, CiphertextDecryptionSelection] = {}

    decryptions: List[Optional[CiphertextDecryptionSelection]] = scheduler.schedule(
        compute_decryption_share_for_selection,
        [(key_pair, selection, context) for selection in contest.selections],
        with_shared_resources=True,
    )

    for decryption in decryptions:
        if decryption is None:
            return None
        selections[decryption.object_id] = decryption

    return CiphertextDecryptionContest(
        contest.object_id,
        key_pair.owner_id,
        contest.description_hash,
        selections,
    )


def compute_compensated_decryption_share_for_contest(
    missing_guardian_coordinate: ElementModQ,
    present_guardian_key: ElectionPublicKey,
    missing_guardian_key: ElectionPublicKey,
    contest: CiphertextContest,
    context: CiphertextElectionContext,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CiphertextCompensatedDecryptionContest]:
    """
    Compute the compensated decryption share for a single contest

    :param missing_guardian_coordinate: Election partial key backup of the missing guardian
    :param guardian_key: The election public key of the available guardian that will partially decrypt the selection
    :param missing_guardian_key: Election public key of the guardian that is missing
    :param contest: The specific contest to decrypt
    :param context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionContest` or `None` if there is an error
    """
    if not scheduler:
        scheduler = Scheduler()

    selections: Dict[SelectionId, CiphertextCompensatedDecryptionSelection] = {}

    selection_decryptions: List[
        Optional[CiphertextCompensatedDecryptionSelection]
    ] = scheduler.schedule(
        compute_compensated_decryption_share_for_selection,
        [
            (
                missing_guardian_coordinate,
                present_guardian_key,
                missing_guardian_key,
                selection,
                context,
            )
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
        present_guardian_key.owner_id,
        missing_guardian_key.owner_id,
        contest.description_hash,
        selections,
    )


def compute_decryption_share_for_selection(
    key_pair: ElectionKeyPair,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
) -> Optional[CiphertextDecryptionSelection]:
    """
    Compute a partial decryption for a specific selection

    :param guardian_keys: Election keys for the guardian who will partially decrypt the selection
    :param selection: The specific selection to decrypt
    :param context: The public election encryption context
    :return: a `CiphertextDecryptionSelection` or `None` if there is an error
    """

    (decryption, proof) = partially_decrypt(
        key_pair, selection.ciphertext, context.crypto_extended_base_hash
    )

    if proof.is_valid(
        selection.ciphertext,
        key_pair.key_pair.public_key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        return create_ciphertext_decryption_selection(
            selection.object_id,
            key_pair.owner_id,
            decryption,
            proof,
        )
    log_warning(
        f"compute decryption share proof failed for guardian {key_pair.owner_id}"
        f"and {selection.object_id} with invalid proof"
    )
    return None


def compute_compensated_decryption_share_for_selection(
    missing_guardian_backup: ElementModQ,
    available_guardian_key: ElectionPublicKey,
    missing_guardian_key: ElectionPublicKey,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
) -> Optional[CiphertextCompensatedDecryptionSelection]:
    """
    Compute a compensated decryption share for a specific selection using the
    available guardian's share of the missing guardian's private key polynomial

    :param missing_guardian_backup: The coordinate aka backup of a missing guardian
    :param available_guardian_key: Election public key of the guardian that is present
    :param missing_guardian_key: Election public key of the guardian that is missing
    :param selection: The specific selection to decrypt
    :param context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionSelection` or `None` if there is an error
    """

    compensated = decrypt_with_threshold(
        missing_guardian_backup,
        selection.ciphertext,
        context.crypto_extended_base_hash,
    )

    if compensated is None:
        log_warning(
            (
                f"compute compensated decryption share failed for {available_guardian_key.owner_id} "
                f"missing: {missing_guardian_key.owner_id} {selection.object_id}"
            )
        )
        return None

    (decryption, proof) = compensated

    recovery_public_key = compute_recovery_public_key(
        available_guardian_key, missing_guardian_key
    )

    if proof.is_valid(
        selection.ciphertext,
        recovery_public_key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        share = CiphertextCompensatedDecryptionSelection(
            selection.object_id,
            available_guardian_key.owner_id,
            missing_guardian_key.owner_id,
            decryption,
            recovery_public_key,
            proof,
        )
        return share
    log_warning(
        (
            f"compute compensated decryption share proof failed for {available_guardian_key.owner_id} "
            f"missing: {missing_guardian_key.owner_id} {selection.object_id}"
        )
    )
    return None


def partially_decrypt(
    key_pair: ElectionKeyPair,
    elgamal: ElGamalCiphertext,
    extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ = None,
) -> Tuple[ElementModP, ChaumPedersenProof]:
    """
    Compute a partial decryption of an elgamal encryption

    :param elgamal: the `ElGamalCiphertext` that will be partially decrypted
    :param extended_base_hash: the extended base hash of the election that
                                was used to generate t he ElGamal Ciphertext
    :param nonce_seed: an optional value used to generate the `ChaumPedersenProof`
                        if no value is provided, a random number will be used.
    :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
    """
    if nonce_seed is None:
        nonce_seed = rand_q()

    # TODO: ISSUE #47: Decrypt the election secret key

    # 𝑀_i = 𝐴^𝑠𝑖 mod 𝑝
    partial_decryption = elgamal.partial_decrypt(key_pair.key_pair.secret_key)

    # 𝑀_i = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
    proof = make_chaum_pedersen(
        message=elgamal,
        s=key_pair.key_pair.secret_key,
        m=partial_decryption,
        seed=nonce_seed,
        hash_header=extended_base_hash,
    )

    return (partial_decryption, proof)


def decrypt_backup(
    guardian_backup: ElectionPartialKeyBackup,
    key_pair: ElectionKeyPair,
) -> Optional[ElementModQ]:
    """
    Decrypts a compensated partial decryption of an elgamal encryption
    on behalf of a missing guardian

    :param guardian_backup: Missing guardian's backup
    :param key_pair: The present guardian's key pair that will be used to decrypt the backup
    :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
    """
    encryption_seed = get_backup_seed(
        key_pair.owner_id,
        key_pair.sequence_order,
    )
    bytes_optional = guardian_backup.encrypted_coordinate.decrypt(
        key_pair.key_pair.secret_key, encryption_seed
    )
    if bytes_optional is None:
        return None
    coordinate_data: CoordinateData = CoordinateData.from_bytes(
        get_optional(bytes_optional)
    )
    return coordinate_data.coordinate


def decrypt_with_threshold(
    coordinate: ElementModQ,
    ciphertext: ElGamalCiphertext,
    extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ = None,
) -> Optional[Tuple[ElementModP, ChaumPedersenProof]]:
    """
    Compute a compensated partial decryption of an elgamal encryption
    given a coordinate from a missing guardian.

    :param coordinate: The coordinate aka backup provided to a present guardian from
                        a missing guardian
    :param ciphertext: the `ElGamalCiphertext` that will be partially decrypted
    :param extended_base_hash: the extended base hash of the election that
                                was used to generate the ElGamal Ciphertext
    :param nonce_seed: an optional value used to generate the `ChaumPedersenProof`
                        if no value is provided, a random number will be used.
    :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
    """
    if nonce_seed is None:
        nonce_seed = rand_q()

    # 𝑀_{𝑖,l} = 𝐴^P𝑖_{l}
    partial_decryption = ciphertext.partial_decrypt(coordinate)

    # 𝑀_{𝑖,l} = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
    proof = make_chaum_pedersen(
        ciphertext,
        coordinate,
        partial_decryption,
        nonce_seed,
        extended_base_hash,
    )

    return (partial_decryption, proof)


def compute_recovery_public_key(
    guardian_key: ElectionPublicKey,
    missing_guardian_key: ElectionPublicKey,
) -> RecoveryPublicKey:
    """
    Compute the recovery public key,
    corresponding to the secret share Pi(l)
    K_ij^(l^j) for j in 0..k-1.  K_ij is coefficients[j].public_key
    """

    pub_key = ONE_MOD_P
    for index, commitment in enumerate(missing_guardian_key.coefficient_commitments):
        exponent = pow_q(guardian_key.sequence_order, index)
        pub_key = mult_p(pub_key, pow_p(commitment, exponent))
    return pub_key


def reconstruct_decryption_share(
    missing_guardian_key: ElectionPublicKey,
    tally: CiphertextTally,
    shares: Dict[GuardianId, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GuardianId, ElementModQ],
) -> DecryptionShare:
    """
    Reconstruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: The public key of the guardian creating share
    :param tally: The collection of `CiphertextTallyContest` that is cast
    :shares: the collection of `CompensatedTallyDecryptionShare` for the missing guardian from available guardians
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    contests: Dict[ContestId, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_key.owner_id,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            shares,
            lagrange_coefficients,
        )

    return DecryptionShare(
        tally.object_id,
        missing_guardian_key.owner_id,
        missing_guardian_key.key,
        contests,
    )


def reconstruct_decryption_share_for_ballot(
    missing_guardian_key: ElectionPublicKey,
    ballot: SubmittedBallot,
    shares: Dict[GuardianId, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GuardianId, ElementModQ],
) -> DecryptionShare:
    """
    Reconstruct a missing ballot Decryption share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param public_key: the public key for the missing guardian
    :param ballot: The `SubmittedBallot` to reconstruct
    :shares: the collection of `CompensatedBallotDecryptionShare` for
        the missing guardian, each keyed by the ID of the guardian that produced it from available guardians
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """
    contests: Dict[ContestId, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_key.owner_id,
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                contest.ballot_selections,
            ),
            shares,
            lagrange_coefficients,
        )

    return DecryptionShare(
        ballot.object_id,
        missing_guardian_key.owner_id,
        missing_guardian_key.key,
        contests,
    )


def reconstruct_decryption_contest(
    missing_guardian_id: GuardianId,
    contest: CiphertextContest,
    shares: Dict[GuardianId, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GuardianId, ElementModQ],
) -> CiphertextDecryptionContest:
    """
    Reconstruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param contest: The CiphertextContest to decrypt
    :shares: the collection of `CompensatedDecryptionShare` for the missing guardian from available guardians
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """

    contest_shares: Dict[GuardianId, CiphertextCompensatedDecryptionContest] = {
        available_guardian_id: compensated_share.contests[contest.object_id]
        for available_guardian_id, compensated_share in shares.items()
    }

    selections: Dict[SelectionId, CiphertextDecryptionSelection] = {}
    for selection in contest.selections:

        # collect all of the shares generated for each selection
        compensated_selection_shares: Dict[
            GuardianId, CiphertextCompensatedDecryptionSelection
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
    available_guardians_keys: List[ElectionPublicKey],
) -> Dict[GuardianId, ElementModQ]:
    """
    Produce all Lagrange coefficients for a collection of available
    Guardians, to be used when reconstructing a missing share.
    """
    return {
        guardian_keys.owner_id: compute_lagrange_coefficients_for_guardian(
            guardian_keys, available_guardians_keys
        )
        for guardian_keys in available_guardians_keys
    }


def compute_lagrange_coefficients_for_guardian(
    guardian_key: ElectionPublicKey,
    other_guardians_keys: List[ElectionPublicKey],
) -> ElementModQ:
    """
    Produce a Lagrange coefficient for a single Guardian, to be used when reconstructing a missing share.
    """
    other_guardian_orders = [
        g.sequence_order
        for g in other_guardians_keys
        if g.owner_id != guardian_key.owner_id
    ]
    return compute_lagrange_coefficient(
        guardian_key.sequence_order,
        *other_guardian_orders,
    )
