from typing import Dict, Optional, Tuple

from .ballot import SubmittedBallot, CiphertextContest, CiphertextSelection
from .decryption_share import (
    CiphertextDecryptionSelection,
    DecryptionShare,
    get_shares_for_selection,
)
from .dlog import discrete_log
from .group import ElementModP, ElementModQ, mult_p, div_p
from .tally import (
    CiphertextTally,
    PlaintextTally,
    PlaintextTallyContest,
    PlaintextTallySelection,
)
from .logs import log_warning
from .types import CONTEST_ID, GUARDIAN_ID, SELECTION_ID

AVAILABLE_GUARDIAN_ID = GUARDIAN_ID
MISSING_GUARDIAN_ID = GUARDIAN_ID

GUARDIAN_PUBLIC_KEY = ElementModP

ELECTION_PUBLIC_KEY = ElementModP

# The methods in this file can be used to decrypt values if private keys or nonces are not known
# and the key ceremony is used to share secrets among a quorum of guardians


def decrypt_tally(
    tally: CiphertextTally,
    shares: Dict[GUARDIAN_ID, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
) -> Optional[PlaintextTally]:
    """
    Try to decrypt the tally and the spoiled ballots using the provided decryption shares
    :param tally: The CiphertextTally to decrypt
    :param shares: The guardian Decryption Shares for all guardians
    :param context: the Ciphertextelectioncontext
    :return: A PlaintextTally or None if there is an error
    """

    contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}

    for contest in tally.contests.values():
        plaintext_contest = decrypt_contest_with_decryption_shares(
            CiphertextContest(
                contest.object_id,
                contest.description_hash,
                list(contest.selections.values()),
            ),
            shares,
            crypto_extended_base_hash,
        )
        if not plaintext_contest:
            return None
        contests[contest.object_id] = plaintext_contest

    return PlaintextTally(tally.object_id, contests)


def decrypt_ballot(
    ballot: SubmittedBallot,
    shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
) -> Optional[PlaintextTally]:
    """
    Try to decrypt a single ballot using the provided decryption shares

    :param ballot: The SubmittedBallot to decrypt
    :param shares: The guardian Decryption Shares for all guardians
    :param crypto_extended_base_hash: The extended base hash
    :return: A PlaintextTally or None if there is an error
    """
    contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}

    for contest in ballot.contests:
        plaintext_contest = decrypt_contest_with_decryption_shares(
            CiphertextContest(
                contest.object_id,
                contest.description_hash,
                contest.ballot_selections,
            ),
            shares,
            crypto_extended_base_hash,
        )
        if not plaintext_contest:
            return None
        contests[contest.object_id] = plaintext_contest

    return PlaintextTally(ballot.object_id, contests)


def decrypt_contest_with_decryption_shares(
    contest: CiphertextContest,
    shares: Dict[GUARDIAN_ID, DecryptionShare],
    crypto_extended_base_hash: ElementModQ,
) -> Optional[PlaintextTallyContest]:
    """
    Decrypt the specified contest within the context of the specified Decryption Shares

    :param contest: the contest to decrypt
    :param shares: a collection of `DecryptionShare` used to decrypt
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a collection of `PlaintextTallyContest` or `None` if there is an error
    """

    plaintext_selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}

    for selection in contest.selections:
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
    shares: Dict[
        GUARDIAN_ID, Tuple[ELECTION_PUBLIC_KEY, CiphertextDecryptionSelection]
    ],
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
                return None

    # accumulate all of the shares calculated for the selection
    all_shares_product_M = mult_p(
        *[decryption.share for (_, decryption) in shares.values()]
    )

    # Calculate 𝑀=𝐵⁄(∏𝑀𝑖) mod 𝑝.
    decrypted_value = div_p(selection.ciphertext.data, all_shares_product_M)
    d_log = discrete_log(decrypted_value)
    return PlaintextTallySelection(
        selection.object_id,
        d_log,
        decrypted_value,
        selection.ciphertext,
        [share for (guardian_id, (public_key, share)) in shares.items()],
    )
