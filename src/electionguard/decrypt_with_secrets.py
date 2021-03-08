from typing import List, Optional

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)
from .group import ElementModP, ElementModQ
from .logs import log_warning
from .manifest import (
    InternalManifest,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .nonces import Nonces

from .utils import get_optional

ELECTION_PUBLIC_KEY = ElementModP

# The Methods in this file can be used to decrypt values if private keys or nonces are known


def decrypt_selection_with_secret(
    selection: CiphertextBallotSelection,
    description: SelectionDescription,
    public_key: ElementModP,
    secret_key: ElementModQ,
    crypto_extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CiphertextBallotSelection` within the context of the specified selection.

    :param selection: the selection to decrypt
    :param description: the qualified selection metadata
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not selection.is_valid_encryption(
        description.crypto_hash(), public_key, crypto_extended_base_hash
    ):
        return None

    plaintext_vote = selection.ciphertext.decrypt(secret_key)

    # TODO: ISSUE #47: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(
        selection.object_id,
        plaintext_vote,
        selection.is_placeholder_selection,
    )


def decrypt_selection_with_nonce(
    selection: CiphertextBallotSelection,
    description: SelectionDescription,
    public_key: ElementModP,
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CiphertextBallotSelection` within the context of the specified selection.

    :param selection: the contest selection to decrypt
    :param description: the qualified selection metadata that may be a placeholder selection
    :param public_key: the public key for the election (K)
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param nonce_seed: the optional nonce that was seeded to the encryption function.
                        if no value is provided, the nonce field from the selection is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not selection.is_valid_encryption(
        description.crypto_hash(), public_key, crypto_extended_base_hash
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

    plaintext_vote = selection.ciphertext.decrypt_known_nonce(public_key, nonce)

    # TODO: ISSUE #35: encrypt/decrypt: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(
        selection.object_id,
        plaintext_vote,
        selection.is_placeholder_selection,
    )


def decrypt_contest_with_secret(
    contest: CiphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    secret_key: ElementModQ,
    crypto_extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CiphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not contest.is_valid_encryption(
        description.crypto_hash(), public_key, crypto_extended_base_hash
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
            crypto_extended_base_hash,
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
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CiphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param nonce_seed: the optional nonce that was seeded to the encryption function
                        if no value is provided, the nonce field from the contest is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not contest.is_valid_encryption(
        description.crypto_hash(), public_key, crypto_extended_base_hash
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
            crypto_extended_base_hash,
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


def decrypt_ballot_with_secret(
    ballot: CiphertextBallot,
    internal_manifest: InternalManifest,
    crypto_extended_base_hash: ElementModQ,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param internal_manifest: the qualified election metadata that includes placeholder selections
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        internal_manifest.manifest_hash, public_key, crypto_extended_base_hash
    ):
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = internal_manifest.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_secret(
            contest,
            get_optional(description),
            public_key,
            secret_key,
            crypto_extended_base_hash,
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

    return PlaintextBallot(ballot.object_id, ballot.style_id, plaintext_contests)


def decrypt_ballot_with_nonce(
    ballot: CiphertextBallot,
    internal_manifest: InternalManifest,
    crypto_extended_base_hash: ElementModQ,
    public_key: ElementModP,
    nonce: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param internal_manifest: the qualified election metadata that includes placeholder selections
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param nonce: the optional master ballot nonce that was either seeded to, or gernated by the encryption function
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        internal_manifest.manifest_hash, public_key, crypto_extended_base_hash
    ):
        return None

    # Use the hashed representation included in the ballot
    # or override with the provided values
    if nonce is None:
        nonce_seed = ballot.hashed_ballot_nonce()
    else:
        nonce_seed = CiphertextBallot.nonce_seed(
            internal_manifest.manifest_hash, ballot.object_id, nonce
        )

    if nonce_seed is None:
        log_warning(
            f"missing nonce_seed value. decrypt could not derive a nonce value for ballot {ballot.object_id}"
        )
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = internal_manifest.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_nonce(
            contest,
            get_optional(description),
            public_key,
            crypto_extended_base_hash,
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

    return PlaintextBallot(ballot.object_id, ballot.style_id, plaintext_contests)
