from typing import Dict, List, Optional, Tuple
from electionguard.chaum_pedersen import ChaumPedersenProof, make_chaum_pedersen

from electionguard.elgamal import ElGamalCiphertext
from electionguard.utils import get_optional

from .auxiliary import AuxiliaryDecrypt, AuxiliaryKeyPair
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
    hex_to_q,
    mult_p,
    pow_p,
    pow_q,
    rand_q,
)
from .key_ceremony import ElectionKeyPair, ElectionPartialKeyBackup, ElectionPublicKey
from .logs import log_warning
from .rsa import rsa_decrypt
from .scheduler import Scheduler
from .tally import CiphertextTally

from .types import CONTEST_ID, GUARDIAN_ID, SELECTION_ID

GUARDIAN_PUBLIC_KEY = ElementModP
ELECTION_PUBLIC_KEY = ElementModP
RECOVERY_PUBLIC_KEY = ElementModP


def compute_decryption_share(
    guardian_keys: ElectionKeyPair,
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

    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_decryption_share_for_contest(
            guardian_keys,
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
        guardian_keys.owner_id,
        guardian_keys.share().key,
        contests,
    )


def compute_compensated_decryption_share(
    guardian_key: ElectionPublicKey,
    guardian_auxiliary_keys: AuxiliaryKeyPair,
    missing_guardian_key: ElectionPublicKey,
    missing_guardian_backup: ElectionPartialKeyBackup,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for all of the contests in the Ciphertext Tally

    :param guardian_key: Guardian's election public key
    :param guardian_auxiliary_keys: Guardian's auxiliary key pair
    :param missing_guardian_key: Missing guardian's election public key
    :param missing_guardian_backup: Missing guardian's election partial key backup
    :param tally: Encrypted tally to get decryption share of
    :param context: Election context
    :param decrypt: Auxiliary decryption method
    :param scheduler: Scheduler
    :return: Return a guardian's compensated decryption share of tally for the missing guardian
        or None if error
    """

    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in tally.contests.values():
        contest_share = compute_compensated_decryption_share_for_contest(
            guardian_key,
            guardian_auxiliary_keys,
            missing_guardian_key,
            missing_guardian_backup,
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
        guardian_key.owner_id,
        missing_guardian_key.owner_id,
        guardian_key.key,
        contests,
    )


def compute_decryption_share_for_ballot(
    guardian_keys: ElectionKeyPair,
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
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_decryption_share_for_contest(
            guardian_keys,
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
        guardian_keys.owner_id,
        guardian_keys.share().key,
        contests,
    )


def compute_compensated_decryption_share_for_ballot(
    guardian_key: ElectionPublicKey,
    guardian_auxiliary_keys: AuxiliaryKeyPair,
    missing_guardian_key: ElectionPublicKey,
    missing_guardian_backup: ElectionPartialKeyBackup,
    ballot: SubmittedBallot,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute the compensated decryption for a single ballot

    :param guardian_key: Guardian's election public key
    :param guardian_auxiliary_keys: Guardian's auxiliary key pair
    :param missing_guardian_key: Missing guardian's election public key
    :param missing_guardian_backup: Missing guardian's election partial key backup
    :param ballot: Encrypted ballot to get decryption share of
    :param context: Election context
    :param decrypt: Auxiliary decryption method
    :param scheduler: Scheduler
    :return: Return a guardian's compensated decryption share of ballot for the missing guardian
        or None if error
    """
    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in ballot.contests:
        contest_share = compute_compensated_decryption_share_for_contest(
            guardian_key,
            guardian_auxiliary_keys,
            missing_guardian_key,
            missing_guardian_backup,
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
        guardian_key.owner_id,
        missing_guardian_key.owner_id,
        guardian_key.key,
        contests,
    )


def compute_decryption_share_for_contest(
    guardian_keys: ElectionKeyPair,
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

    selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}

    decryptions: List[Optional[CiphertextDecryptionSelection]] = scheduler.schedule(
        compute_decryption_share_for_selection,
        [(guardian_keys, selection, context) for selection in contest.selections],
        with_shared_resources=True,
    )

    for decryption in decryptions:
        if decryption is None:
            return None
        selections[decryption.object_id] = decryption

    return CiphertextDecryptionContest(
        contest.object_id,
        guardian_keys.owner_id,
        contest.description_hash,
        selections,
    )


def compute_compensated_decryption_share_for_contest(
    guardian_key: ElectionPublicKey,
    guardian_auxiliary_keys: AuxiliaryKeyPair,
    missing_guardian_key: ElectionPublicKey,
    missing_guardian_backup: ElectionPartialKeyBackup,
    contest: CiphertextContest,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
    scheduler: Optional[Scheduler] = None,
) -> Optional[CiphertextCompensatedDecryptionContest]:
    """
    Compute the compensated decryption share for a single contest

    :param guardian_key: The election public key of the available guardian that will partially decrypt the selection
    :param guardian_auxiliary_keys: Auxiliary keys for the available guardian
    :param missing_guardian_key: Election public key of the guardian that is missing
    :param missing_guardian_backup: Election partial key backup of the missing guardian
    :param contest: The specific contest to decrypt
    :param context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionContest` or `None` if there is an error
    """
    if not scheduler:
        scheduler = Scheduler()

    selections: Dict[SELECTION_ID, CiphertextCompensatedDecryptionSelection] = {}

    selection_decryptions: List[
        Optional[CiphertextCompensatedDecryptionSelection]
    ] = scheduler.schedule(
        compute_compensated_decryption_share_for_selection,
        [
            (
                guardian_key,
                guardian_auxiliary_keys,
                missing_guardian_key,
                missing_guardian_backup,
                selection,
                context,
                decrypt,
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
        guardian_key.owner_id,
        missing_guardian_key.owner_id,
        contest.description_hash,
        selections,
    )


def compute_decryption_share_for_selection(
    guardian_keys: ElectionKeyPair,
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
        guardian_keys, selection.ciphertext, context.crypto_extended_base_hash
    )

    if proof.is_valid(
        selection.ciphertext,
        guardian_keys.key_pair.public_key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        return create_ciphertext_decryption_selection(
            selection.object_id,
            guardian_keys.owner_id,
            decryption,
            proof,
        )
    log_warning(
        f"compute decryption share proof failed for guardian {guardian_keys.owner_id}"
        f"and {selection.object_id} with invalid proof"
    )
    return None


def compute_compensated_decryption_share_for_selection(
    guardian_key: ElectionPublicKey,
    guardian_auxiliary_keys: AuxiliaryKeyPair,
    missing_guardian_key: ElectionPublicKey,
    missing_guardian_backup: ElectionPartialKeyBackup,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
) -> Optional[CiphertextCompensatedDecryptionSelection]:
    """
    Compute a compensated decryption share for a specific selection using the
    available guardian's share of the missing guardian's private key polynomial

    :param guardian_key: The election public key of the available guardian that will partially decrypt the selection
    :param guardian_auxiliary_keys: Auxiliary keys for the available guardian
    :param missing_guardian_key: Election public key of the guardian that is missing
    :param missing_guardian_backup: Election partial key backup of the missing guardian
    :param selection: The specific selection to decrypt
    :param context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionSelection` or `None` if there is an error
    """

    compensated = compensate_decrypt(
        guardian_auxiliary_keys,
        missing_guardian_backup,
        selection.ciphertext,
        context.crypto_extended_base_hash,
        decrypt=decrypt,
    )

    if compensated is None:
        log_warning(
            (
                f"compute compensated decryption share failed for {guardian_auxiliary_keys.owner_id} "
                f"missing: {missing_guardian_key.owner_id} {selection.object_id}"
            )
        )
        return None

    (decryption, proof) = compensated

    recovery_public_key = compute_recovery_public_key(
        guardian_key, missing_guardian_key
    )

    if recovery_public_key is None:
        log_warning(
            (
                f"compute compensated decryption share failed for {guardian_key.owner_id} "
                f"missing recovery key: {missing_guardian_key.owner_id} {selection.object_id}"
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
            guardian_key.owner_id,
            missing_guardian_key.owner_id,
            decryption,
            recovery_public_key,
            proof,
        )
        return share
    log_warning(
        (
            f"compute compensated decryption share proof failed for {guardian_key.owner_id} "
            f"missing: {missing_guardian_key.owner_id} {selection.object_id}"
        )
    )
    return None


def partially_decrypt(
    guardian_keys: ElectionKeyPair,
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
    partial_decryption = elgamal.partial_decrypt(guardian_keys.key_pair.secret_key)

    # 𝑀_i = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
    proof = make_chaum_pedersen(
        message=elgamal,
        s=guardian_keys.key_pair.secret_key,
        m=partial_decryption,
        seed=nonce_seed,
        hash_header=extended_base_hash,
    )

    return (partial_decryption, proof)


def compensate_decrypt(
    guardian_auxiliary_keys: AuxiliaryKeyPair,
    missing_guardian_backup: ElectionPartialKeyBackup,
    ciphertext: ElGamalCiphertext,
    extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ = None,
    decrypt: AuxiliaryDecrypt = rsa_decrypt,
) -> Optional[Tuple[ElementModP, ChaumPedersenProof]]:
    """
    Compute a compensated partial decryption of an elgamal encryption
    on behalf of the missing guardian

    :param guardian_auxiliary_keys: Auxiliary key pair for guardian decrypting
    :param missing_guardian_backup: Missing guardians backup
    :param ciphertext: the `ElGamalCiphertext` that will be partially decrypted
    :param extended_base_hash: the extended base hash of the election that
                                was used to generate t he ElGamal Ciphertext
    :param nonce_seed: an optional value used to generate the `ChaumPedersenProof`
                        if no value is provided, a random number will be used.
    :param decrypt: an `AuxiliaryDecrypt` function to decrypt the missing guardina private key backup
    :return: a `Tuple[ElementModP, ChaumPedersenProof]` of the decryption and its proof
    """
    if nonce_seed is None:
        nonce_seed = rand_q()

    decrypted_value = decrypt(
        missing_guardian_backup.encrypted_value, guardian_auxiliary_keys.secret_key
    )
    if decrypted_value is None:
        log_warning(
            (
                f"compensate decrypt guardian {guardian_auxiliary_keys.owner_id}"
                f" failed decryption for {missing_guardian_backup.owner_id}"
            )
        )
        return None
    partial_secret_key = get_optional(hex_to_q(decrypted_value))

    # 𝑀_{𝑖,l} = 𝐴^P𝑖_{l}
    partial_decryption = ciphertext.partial_decrypt(partial_secret_key)

    # 𝑀_{𝑖,l} = 𝐴^𝑠𝑖 mod 𝑝 and 𝐾𝑖 = 𝑔^𝑠𝑖 mod 𝑝
    proof = make_chaum_pedersen(
        ciphertext,
        partial_secret_key,
        partial_decryption,
        nonce_seed,
        extended_base_hash,
    )

    return (partial_decryption, proof)


def compute_recovery_public_key(
    guardian_key: ElectionPublicKey,
    missing_guardian_key: ElectionPublicKey,
) -> RECOVERY_PUBLIC_KEY:
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
    shares: Dict[GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GUARDIAN_ID, ElementModQ],
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
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in tally.contests.values():
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_key.owner_id,
            CiphertextContest(
                contest.object_id,
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
    shares: Dict[GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GUARDIAN_ID, ElementModQ],
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
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in ballot.contests:
        contests[contest.object_id] = reconstruct_decryption_contest(
            missing_guardian_key.owner_id,
            CiphertextContest(
                contest.object_id, contest.description_hash, contest.ballot_selections
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
    missing_guardian_id: GUARDIAN_ID,
    contest: CiphertextContest,
    shares: Dict[GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[GUARDIAN_ID, ElementModQ],
) -> CiphertextDecryptionContest:
    """
    Recontruct the missing Decryption Share for a missing guardian
    from the collection of compensated decryption shares

    :param missing_guardian_id: The guardian id for the missing guardian
    :param contest: The CiphertextContest to decrypt
    :shares: the collection of `CompensatedDecryptionShare` for the missing guardian from available guardians
    :lagrange_coefficients: the lagrange coefficients corresponding to the available guardians that provided shares
    """

    contest_shares: Dict[GUARDIAN_ID, CiphertextCompensatedDecryptionContest] = {
        available_guardian_id: compensated_share.contests[contest.object_id]
        for available_guardian_id, compensated_share in shares.items()
    }

    selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
    for selection in contest.selections:

        # collect all of the shares generated for each selection
        compensated_selection_shares: Dict[
            GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
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
) -> Dict[GUARDIAN_ID, ElementModQ]:
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
