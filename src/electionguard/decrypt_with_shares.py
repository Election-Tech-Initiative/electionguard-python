from typing import Dict, Optional, Tuple

from .ballot import CiphertextAcceptedBallot, CiphertextSelection
from .decryption_share import (
    TallyDecryptionShare,
    CiphertextDecryptionSelection,
    get_spoiled_shares_for_selection,
    get_tally_shares_for_selection,
)
from .dlog import discrete_log
from .election import CiphertextElectionContext
from .group import ElementModP, ElementModQ, mult_p, div_p
from .tally import (
    CiphertextTally,
    PlaintextTally,
    CiphertextTallyContest,
    PlaintextTallyContest,
    PlaintextTallySelection,
)
from .logs import log_warning
from .types import BALLOT_ID, CONTEST_ID, GUARDIAN_ID, SELECTION_ID

AVAILABLE_GUARDIAN_ID = GUARDIAN_ID
MISSING_GUARDIAN_ID = GUARDIAN_ID

GUARDIAN_PUBLIC_KEY = ElementModP

ELECTION_PUBLIC_KEY = ElementModP

# The methods in this file can be used to decrypt values if private keys or nonces are not known
# and the key ceremony is used to share secrets among a quorum of guardians


def decrypt_selection_with_decryption_shares(
    selection: CiphertextSelection,
    shares: Dict[
        GUARDIAN_ID, Tuple[ELECTION_PUBLIC_KEY, CiphertextDecryptionSelection]
    ],
    extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextTallySelection]:
    """
    Decrypt the specified `CiphertextTallySelection` with the collection of `ElementModP` decryption shares.
    Each share is expected to be passed with the corresponding public key so that the encryption can be validated

    :param selection: a `CiphertextTallySelection`
    :param shares: the collection of shares to decrypt the selection
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a `PlaintextTallySelection` or `None` if there is an error
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check:
        # Verify that all of the shares are computed correctly
        for guardian_id, share in shares.items():
            public_key, decryption = share
            # verify we have a proof or recovered parts
            if not decryption.is_valid(
                selection.ciphertext, public_key, extended_base_hash
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


def decrypt_tally_contests_with_decryption_shares(
    tally: Dict[CONTEST_ID, CiphertextTallyContest],
    shares: Dict[GUARDIAN_ID, TallyDecryptionShare],
    extended_base_hash: ElementModQ,
) -> Optional[Dict[CONTEST_ID, PlaintextTallyContest]]:
    """
    Decrypt the specified tally within the context of the specified Decryption Shares

    :param tally: the encrypted tally of contests
    :param shares: a collection of `TallyDecryptionShare` used to decrypt
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a collection of `PlaintextTallyContest` or `None` if there is an error
    """
    contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}

    # iterate through the tally contests
    for contest in tally.values():
        selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}

        for selection in contest.tally_selections.values():
            tally_shares = get_tally_shares_for_selection(selection.object_id, shares)
            plaintext_selection = decrypt_selection_with_decryption_shares(
                selection, tally_shares, extended_base_hash
            )
            if plaintext_selection is None:
                log_warning(f"could not decrypt tally for contest {contest.object_id}")
                return None
            selections[plaintext_selection.object_id] = plaintext_selection

        contests[contest.object_id] = PlaintextTallyContest(
            contest.object_id, selections
        )

    return contests


def decrypt_tally(
    tally: CiphertextTally,
    shares: Dict[GUARDIAN_ID, TallyDecryptionShare],
    context: CiphertextElectionContext,
) -> Optional[PlaintextTally]:
    """
    Try to decrypt the tally and the spoiled ballots using the provided decryption shares
    :param tally: The CiphertextTally to decrypt
    :param shares: The guardian Decryption Shares for all guardians
    :param context: the Ciphertextelectioncontext
    :return: A PlaintextTally or None if there is an error
    """
    contests = decrypt_tally_contests_with_decryption_shares(
        tally.cast, shares, context.crypto_extended_base_hash
    )

    if contests is None:
        return None

    spoiled_ballots = decrypt_spoiled_ballots(
        tally.spoiled_ballots, shares, context.crypto_extended_base_hash
    )

    if spoiled_ballots is None:
        return None

    return PlaintextTally(tally.object_id, contests, spoiled_ballots)


def decrypt_spoiled_ballots(
    spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
    shares: Dict[AVAILABLE_GUARDIAN_ID, TallyDecryptionShare],
    extended_base_hash: ElementModQ,
) -> Optional[Dict[BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]]]:
    """
    Try to decrypt each of the spoiled ballots using the provided decryption shares
    """

    plaintext_spoiled_ballots: Dict[
        BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]
    ] = {}

    for spoiled_ballot in spoiled_ballots.values():
        contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}
        for contest in spoiled_ballot.contests:
            selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}
            for selection in contest.ballot_selections:
                spoiled_shares = get_spoiled_shares_for_selection(
                    spoiled_ballot.object_id, selection.object_id, shares
                )
                plaintext_selection = decrypt_selection_with_decryption_shares(
                    selection, spoiled_shares, extended_base_hash
                )

                # verify the plaintext values are received and add them to the collection
                if plaintext_selection is None:
                    log_warning(
                        f"could not decrypt spoiled ballot {spoiled_ballot.object_id} for contest {contest.object_id} selection {selection.object_id}"
                    )
                    return None
                selections[plaintext_selection.object_id] = plaintext_selection

            contests[contest.object_id] = PlaintextTallyContest(
                contest.object_id, selections
            )
        plaintext_spoiled_ballots[spoiled_ballot.object_id] = contests

    return plaintext_spoiled_ballots
