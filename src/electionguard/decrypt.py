from typing import Dict, List, Optional, Tuple, Union
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)
from .decryption_share import (
    CiphertextDecryptionSelection,
    DecryptionShare,
    get_tally_shares_for_selection,
)
from .dlog import discrete_log
from .election import (
    InternalElectionDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .group import ElementModP, ElementModQ, mult_p, div_p
from .hash import hash_elems
from .logs import log_warning
from .nonces import Nonces

# from .process import GlobalProcessingPool, CPU_POOL
from .tally import (
    CiphertextTallyContest,
    PlaintextTallyContest,
    CiphertextTallySelection,
    PlaintextTallySelection,
)
from .types import CONTEST_ID, GUARDIAN_ID, SELECTION_ID
from .utils import get_optional

ELECTION_PUBLIC_KEY = ElementModP

# TODO: split this into two files, one decrypt with secrets, the other decrypt with guardians

CiphertextSelection = Union[CiphertextBallotSelection, CiphertextTallySelection]


def decrypt_selection_with_decryption_shares(
    selection: CiphertextSelection,
    shares: Dict[
        GUARDIAN_ID, Tuple[ELECTION_PUBLIC_KEY, CiphertextDecryptionSelection]
    ],
    extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextTallySelection]:
    """
    Decrypt the specified `CiphertextTallySelection` with the collection of `ElementModP` decryption shares

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
            if decryption.proof is None and decryption.recovered_parts is None:
                log_warning(
                    f"decrypt selection failed for guardian: {guardian_id} selection: {selection.object_id} with missing data"
                )
                return None

            if decryption.proof is not None and decryption.recovered_parts is not None:
                log_warning(
                    f"decrypt selection failed for guardian: {guardian_id} selection: {selection.object_id} cannot have proof and recovery"
                )
                return None

            if decryption.proof is not None and not decryption.proof.is_valid(
                selection.message, public_key, decryption.share, extended_base_hash,
            ):
                log_warning(
                    f"decrypt selection failed for guardian: {guardian_id} selection: {selection.object_id} with invalid proof"
                )
                return None

            if decryption.recovered_parts is not None:
                for (
                    compensating_guardian_id,
                    part,
                ) in decryption.recovered_parts.items():
                    if not part.proof.is_valid(
                        selection.message,
                        part.recovery_key,
                        part.share,
                        extended_base_hash,
                    ):

                        log_warning(
                            f"decrypt selection failed for guardian: {guardian_id} selection: {selection.object_id} with invalid partial proof"
                        )
                        return None

    # accumulate all of the shares calculated for the selection
    all_shares_product_M = mult_p(
        *[decryption.share for (_, decryption) in shares.values()]
    )

    # Calculate 𝑀=𝐵⁄(∏𝑀𝑖) mod 𝑝.
    decrypted_value = div_p(selection.message.beta, all_shares_product_M)
    d_log = discrete_log(decrypted_value)
    return PlaintextTallySelection(
        selection.object_id, d_log, decrypted_value, selection.message,
    )


def decrypt_selection_with_secret(
    selection: CiphertextBallotSelection,
    description: SelectionDescription,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CiphertextBallotSelection` within the context of the specified selection.

    :param selection: the selection to decrypt
    :param description: the qualified selection metadata
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not selection.is_valid_encryption(
        description.crypto_hash(), public_key
    ):
        return None

    plaintext = selection.message.decrypt(secret_key)

    # TODO: ISSUE #47: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(
        selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection
    )


def decrypt_selection_with_nonce(
    selection: CiphertextBallotSelection,
    description: SelectionDescription,
    public_key: ElementModP,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CiphertextBallotSelection` within the context of the specified selection.

    :param selection: the contest selection to decrypt
    :param description: the qualified selection metadata that may be a placeholder selection
    :param public_key: the public key for the election (K)
    :param nonce_seed: the optional nonce that was seeded to the encryption function.
                        if no value is provided, the nonce field from the selection is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not selection.is_valid_encryption(
        description.crypto_hash(), public_key
    ):
        return None

    if nonce_seed is None:
        nonce = selection.nonce
    else:
        nonce_sequence = Nonces(description.crypto_hash(), nonce_seed)
        nonce = nonce_sequence[description.sequence_order]

    if nonce is None:
        log_warning(
            f"missing nonce value.  decrypt could not derive a nonce value for selection {selection.object_id}"
        )
        return None

    if selection.nonce is not None and nonce != selection.nonce:
        log_warning(
            f"decrypt could not verify a nonce value for selection {selection.object_id}"
        )
        return None

    plaintext = selection.message.decrypt_known_nonce(public_key, nonce)

    # TODO: ISSUE #35: encrypt/decrypt: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(
        selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection
    )


def decrypt_contest_with_secret(
    contest: CiphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CiphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not contest.is_valid_encryption(
        description.crypto_hash(), public_key
    ):
        return None

    plaintext_selections: List[PlaintextBallotSelection] = list()
    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection = decrypt_selection_with_secret(
            selection,
            get_optional(selection_description),
            public_key,
            secret_key,
            suppress_validity_check,
        )
        if plaintext_selection is not None:
            if (
                not remove_placeholders
                or not plaintext_selection.is_placeholder_selection
            ):
                plaintext_selections.append(plaintext_selection)
        else:
            log_warning(
                f"decryption with secret failed for contest: {contest.object_id} selection: {selection.object_id}"
            )
            return None

    return PlaintextBallotContest(contest.object_id, plaintext_selections)


def decrypt_contest_with_nonce(
    contest: CiphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CiphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param nonce_seed: the optional nonce that was seeded to the encryption function
                        if no value is provided, the nonce field from the contest is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not contest.is_valid_encryption(
        description.crypto_hash(), public_key
    ):
        return None

    if nonce_seed is None:
        nonce_seed = contest.nonce
    else:
        nonce_sequence = Nonces(description.crypto_hash(), nonce_seed)
        nonce_seed = nonce_sequence[description.sequence_order]

    if nonce_seed is None:
        log_warning(
            f"missing nonce_seed value.  decrypt could not dewrive a nonce value for contest {contest.object_id}"
        )
        return None

    if contest.nonce is not None and nonce_seed != contest.nonce:
        log_warning(
            f"decrypt could not verify a nonce_seed value for contest {contest.object_id}"
        )
        return None

    plaintext_selections: List[PlaintextBallotSelection] = list()
    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection = decrypt_selection_with_nonce(
            selection,
            get_optional(selection_description),
            public_key,
            nonce_seed,
            suppress_validity_check,
        )
        if plaintext_selection is not None:
            if (
                not remove_placeholders
                or not plaintext_selection.is_placeholder_selection
            ):
                plaintext_selections.append(plaintext_selection)
        else:
            log_warning(
                f"decryption with nonce failed for contest: {contest.object_id} selection: {selection.object_id}"
            )
            return None

    return PlaintextBallotContest(contest.object_id, plaintext_selections)


def decrypt_tally_contests_with_decryption_shares_async(
    tally: Dict[CONTEST_ID, CiphertextTallyContest],
    shares: Dict[GUARDIAN_ID, DecryptionShare],
    extended_base_hash: ElementModQ,
) -> Optional[Dict[CONTEST_ID, PlaintextTallyContest]]:
    """
    Decrypt the specified tally within the context of the specified Decryption Shares

    :param tally: the encrypted tally of contests
    :param shares: a collection of `DecryptionShare` used to decrypt
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a collection of `PlaintextTallyContest` or `None` if there is an error
    """
    contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}

    cpu_pool = Pool(cpu_count())

    # iterate through the tally contests
    for contest in tally.values():
        selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}

        plaintext_selections = cpu_pool.starmap(
            decrypt_selection_with_decryption_shares,
            [
                (
                    selection,
                    get_tally_shares_for_selection(selection.object_id, shares),
                    extended_base_hash,
                )
                for (_, selection) in contest.tally_selections.items()
            ],
        )

        # verify the plaintext values are received and add them to the collection
        for plaintext in plaintext_selections:
            if plaintext is None:
                log_warning(f"could not decrypt tally for contest {contest.object_id}")
                return None
            selections[plaintext.object_id] = plaintext

        contests[contest.object_id] = PlaintextTallyContest(
            contest.object_id, selections
        )

    cpu_pool.close()

    return contests


def decrypt_tally_contests_with_decryption_shares(
    tally: Dict[CONTEST_ID, CiphertextTallyContest],
    shares: Dict[GUARDIAN_ID, DecryptionShare],
    extended_base_hash: ElementModQ,
) -> Optional[Dict[CONTEST_ID, PlaintextTallyContest]]:
    """
    Decrypt the specified tally within the context of the specified Decryption Shares

    :param tally: the encrypted tally of contests
    :param shares: a collection of `DecryptionShare` used to decrypt
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :return: a collection of `PlaintextTallyContest` or `None` if there is an error
    """
    contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}

    # iterate through the tally contests
    for contest in tally.values():
        selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}

        for (_, selection) in contest.tally_selections.items():
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


def decrypt_ballot_with_secret(
    ballot: CiphertextBallot,
    election_metadata: InternalElectionDescription,
    extended_base_hash: ElementModQ,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        extended_base_hash, public_key
    ):
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_secret(
            contest,
            get_optional(description),
            public_key,
            secret_key,
            suppress_validity_check,
            remove_placeholders,
        )
        if plaintext_contest is not None:
            plaintext_contests.append(plaintext_contest)
        else:
            log_warning(
                f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}"
            )
            return None

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)


def decrypt_ballot_with_nonce(
    ballot: CiphertextBallot,
    election_metadata: InternalElectionDescription,
    extended_base_hash: ElementModQ,
    public_key: ElementModP,
    nonce: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param nonce: the optional master ballot nonce that was either seeded to, or gernated by the encryption function
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        extended_base_hash, public_key
    ):
        return None

    # Use the hashed representation included in the ballot
    # or override with the provided values
    if nonce is None:
        nonce_seed = ballot.hashed_ballot_nonce
    else:
        nonce_seed = hash_elems(extended_base_hash, ballot.object_id, nonce)

    if nonce_seed is None:
        log_warning(
            f"missing nonce_seed value. decrypt could not derive a nonce value for ballot {ballot.object_id}"
        )
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_nonce(
            contest,
            get_optional(description),
            public_key,
            nonce_seed,
            suppress_validity_check,
            remove_placeholders,
        )
        if plaintext_contest is not None:
            plaintext_contests.append(plaintext_contest)
        else:
            log_warning(
                f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}"
            )
            return None

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)
