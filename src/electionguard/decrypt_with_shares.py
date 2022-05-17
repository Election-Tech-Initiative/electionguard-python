from typing import Dict, Optional, Tuple


from .ballot import SubmittedBallot, CiphertextContest, CiphertextSelection
from .decryption_share import (
    CiphertextDecryptionSelection,
    DecryptionShare,
    get_shares_for_selection,
)
from .discrete_log import DiscreteLog
from .group import ElementModP, ElementModQ, mult_p, div_p
from .logs import log_warning
from .manifest import (
    ContestDescription,
    Manifest,
)
from .tally import (
    CiphertextTally,
    PlaintextTally,
    PlaintextTallyContest,
    PlaintextTallySelection,
)
from .type import ContestId, GuardianId, SelectionId

# The methods in this file can be used to decrypt values if private keys or nonces are not known
# and the key ceremony is used to share secrets among a quorum of guardians


def decrypt_tally(
    tally: CiphertextTally,
    shares: Dict[GuardianId, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
    manifest: Manifest,
    remove_placeholders: bool = True,
) -> Optional[PlaintextTally]:
    """
    Try to decrypt the tally and the spoiled ballots using the provided decryption shares.

    :param tally: The CiphertextTally to decrypt
    :param shares: The guardian Decryption Shares for all guardians
    :param context: the Ciphertextelectioncontext
    :return: A PlaintextTally or None if there is an error
    """
    contests: Dict[ContestId, PlaintextTallyContest] = {}
    contest_descriptions = {
        description.object_id: description for description in manifest.contests
    }

    for contest in tally.contests.values():
        if contest.object_id not in contest_descriptions.keys():
            continue  # Skip contests not in manifest

        plaintext_contest = decrypt_contest_with_decryption_shares(
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            shares,
            crypto_extended_base_hash,
            contest_descriptions[contest.object_id],
            remove_placeholders,
        )
        if not plaintext_contest:
            log_warning(f"contest: {contest.object_id} failed to decrypt with shares")
            return None
        contests[contest.object_id] = plaintext_contest

    return PlaintextTally(tally.object_id, contests)


def decrypt_ballot(
    ballot: SubmittedBallot,
    shares: Dict[GuardianId, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
    manifest: Manifest,
    remove_placeholders: bool = True,
) -> Optional[PlaintextTally]:
    """
    Try to decrypt a single ballot using the provided decryption shares.

    :param ballot: The SubmittedBallot to decrypt
    :param shares: The guardian Decryption Shares for all guardians
    :param crypto_extended_base_hash: The extended base hash
    :return: A PlaintextTally or None if there is an error
    """
    contests: Dict[ContestId, PlaintextTallyContest] = {}
    contest_descriptions = {
        description.object_id: description for description in manifest.contests
    }

    for contest in ballot.contests:
        if contest.object_id not in contest_descriptions.keys():
            continue  # Skip contests not in manifest

        plaintext_contest = decrypt_contest_with_decryption_shares(
            CiphertextContest(
                contest.object_id,
                contest.sequence_order,
                contest.description_hash,
                contest.ballot_selections,
            ),
            shares,
            crypto_extended_base_hash,
            contest_descriptions[contest.object_id],
            remove_placeholders,
        )
        if not plaintext_contest:
            log_warning(f"contest: {contest.object_id} failed to decrypt with shares")
            return None
        contests[contest.object_id] = plaintext_contest

    return PlaintextTally(ballot.object_id, contests)


def decrypt_contest_with_decryption_shares(
    contest: CiphertextContest,
    shares: Dict[GuardianId, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
    contest_description: ContestDescription,
    remove_placeholders: bool = True,
) -> Optional[PlaintextTallyContest]:
    """
    Decrypt the specified contest within the context of the specified Decryption Shares.

    :param contest: the contest to decrypt
    :param shares: a collection of `DecryptionShare` used to decrypt
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a collection of `PlaintextTallyContest` or `None` if there is an error
    """
    plaintext_selections: Dict[SelectionId, PlaintextTallySelection] = {}
    selection_description_ids = [
        description.object_id for description in contest_description.ballot_selections
    ]

    for selection in contest.selections:
        if selection.object_id not in selection_description_ids and remove_placeholders:
            continue  # Skip selections not in manifest (Such as placeholders)

        tally_shares = get_shares_for_selection(selection.object_id, shares)
        plaintext_selection = decrypt_selection_with_decryption_shares(
            selection, tally_shares, crypto_extended_base_hash
        )
        if plaintext_selection is None:
            log_warning(
                (
                    f"could not decrypt contest {contest.object_id} "
                    f"with selection {selection.object_id}"
                )
            )
            return None
        plaintext_selections[plaintext_selection.object_id] = plaintext_selection

    return PlaintextTallyContest(contest.object_id, plaintext_selections)


def decrypt_selection_with_decryption_shares(
    selection: CiphertextSelection,
    shares: Dict[GuardianId, Tuple[ElementModP, CiphertextDecryptionSelection]],
    crypto_extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextTallySelection]:
    """
    Decrypt the specified `CiphertextSelection` with the collection of `ElementModP` decryption shares.
    Each share is expected to be passed with the corresponding public key so that the encryption can be validated

    :param selection: a `CiphertextSelection`
    :param shares: the collection of shares to decrypt the selection
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :return: a `PlaintextTallySelection` or `None` if there is an error
    """
    if not suppress_validity_check:
        # Verify that all of the shares are computed correctly
        for share in shares.values():
            public_key, decryption = share
            # verify we have a proof or recovered parts
            if not decryption.is_valid(
                selection.ciphertext, public_key, crypto_extended_base_hash
            ):
                log_warning(
                    f"share: {decryption.object_id} has invalid proof or recovered parts"
                )
                return None

    # accumulate all of the shares calculated for the selection
    all_shares_product_M = mult_p(
        *[decryption.share for (_, decryption) in shares.values()]
    )

    # Calculate 𝑀=𝐵⁄(∏𝑀𝑖) mod 𝑝.
    decrypted_value = div_p(selection.ciphertext.data, all_shares_product_M)
    d_log = DiscreteLog().discrete_log(decrypted_value)
    return PlaintextTallySelection(
        selection.object_id,
        d_log,
        decrypted_value,
        selection.ciphertext,
        [share for (guardian_id, (public_key, share)) in shares.items()],
    )
