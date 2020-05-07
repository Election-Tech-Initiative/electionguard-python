from typing import Optional, List

from .ballot import (
    CyphertextBallot,
    CyphertextBallotContest,
    CyphertextBallotSelection,
    PlaintextBallot, 
    PlaintextBallotContest, 
    PlaintextBallotSelection,
    hashed_ballot_nonce
)

from .election import (
    InternalElectionDescription,
    ContestDescriptionWithPlaceholders, 
    SelectionDescription
)

from .group import ElementModP, ElementModQ
from .logs import log_warning
from .nonces import Nonces
from .utils import unwrap_optional

def decrypt_selection_with_secret(
    selection: CyphertextBallotSelection, 
    description: SelectionDescription,
    public_key: ElementModP, 
    secret_key: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CyphertextBallotSelection` within the context of the specified selection.

    :param selection: the selection to decrypt
    :param description: the qualified selection metadata
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """
    
    if not suppress_validity_check and not selection.is_valid_encryption(description.crypto_hash(), public_key):
            return None

    plaintext = selection.message.decrypt(secret_key)

    # TODO: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection)

def decrypt_selection_with_nonce(
    selection: CyphertextBallotSelection, 
    description: SelectionDescription,
    public_key: ElementModP,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotSelection]:
    """
    Decrypt the specified `CyphertextBallotSelection` within the context of the specified selection.

    :param contest: the contest to decrypt
    :param description: the qualified selection metadata that may be a placeholder selection
    :param public_key: the public key for the election (K)
    :param nonce_seed: the optional nonce that was seeded to the encryption function.
                        if no value is provided, the nonce field from the selection is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """
    
    if not suppress_validity_check and not selection.is_valid_encryption(description.crypto_hash(), public_key):
            return None

    if nonce_seed is None:
        nonce = selection.nonce
    else:
        nonce_sequence = Nonces(description.crypto_hash(), nonce_seed)
        nonce = nonce_sequence[description.sequence_order]

    if nonce is None:
        log_warning(f"missing nonce value.  decrypt could not dewrive a nonce value for selection {selection.object_id}")
        return None

    plaintext = selection.message.decrypt_known_nonce(public_key, nonce)

    # TODO: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection)

def decrypt_contest_with_secret(
    contest: CyphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CyphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not contest.is_valid_encryption(description.crypto_hash(), public_key):
        return None
    
    plaintext_selections: List[PlaintextBallotSelection] = list()
    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection = decrypt_selection_with_secret(
                selection, 
                unwrap_optional(selection_description), 
                public_key, 
                secret_key, 
                suppress_validity_check
            )
        if plaintext_selection is not None: 
            plaintext_selections.append(plaintext_selection)
        else:
            log_warning(f"decryption with secret failed for contest: {contest.object_id} selection: {selection.object_id}")

    return PlaintextBallotContest(contest.object_id, plaintext_selections)

def decrypt_contest_with_nonce(
    contest: CyphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    nonce_seed: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotContest]:
    """
    Decrypt the specified `CyphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param nonce_seed: the optional nonce that was seeded to the encryption function
                        if no value is provided, the nonce field from the contest is used
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not contest.is_valid_encryption(description.crypto_hash(), public_key):
        return None

    if nonce_seed is None:
        nonce_seed = contest.nonce
    else:
        nonce_sequence = Nonces(description.crypto_hash(), nonce_seed)
        nonce_seed = nonce_sequence[description.sequence_order]

    if nonce_seed is None:
        log_warning(f"missing nonce_seed value.  decrypt could not dewrive a nonce value for contest {contest.object_id}")
        return None
    
    plaintext_selections: List[PlaintextBallotSelection] = list()
    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection = decrypt_selection_with_nonce(
                selection, 
                unwrap_optional(selection_description), 
                public_key, 
                nonce_seed, 
                suppress_validity_check
            )
        if plaintext_selection is not None: 
            plaintext_selections.append(plaintext_selection)
        else:
            log_warning(f"decryption with nonce failed for contest: {contest.object_id} selection: {selection.object_id}")

    return PlaintextBallotContest(contest.object_id, plaintext_selections)

def decrypt_ballot_with_secret(
    ballot: CyphertextBallot,
    election_metadata: InternalElectionDescription,
    extended_base_hash: ElementModQ,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CyphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(extended_base_hash, public_key):
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_secret(
            contest,
            unwrap_optional(description),
            public_key,
            secret_key,
            suppress_validity_check
        )
        if plaintext_contest is not None: 
            plaintext_contests.append(plaintext_contest)
        else:
            log_warning(f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}")

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)

def decrypt_ballot_with_nonce(
    ballot: CyphertextBallot,
    election_metadata: InternalElectionDescription,
    extended_base_hash: ElementModQ,
    public_key: ElementModP,
    nonce: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CyphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param nonce: the optional master ballot nonce that was either seeded to, or gernated by the encryption function
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(extended_base_hash, public_key):
        return None

    # Use the hashed representation included in the ballot
    # or override with the provided values
    if nonce is None:
        nonce_seed = ballot.hashed_ballot_nonce
    else:
        nonce_seed = hashed_ballot_nonce(
            extended_base_hash, ballot.object_id, nonce
        )

    if nonce_seed is None:
        log_warning(f"missing nonce_seed value.  decrypt could not dewrive a nonce value for ballot {ballot.object_id}")
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_nonce(
            contest,
            unwrap_optional(description),
            public_key,
            nonce_seed,
            suppress_validity_check
        )
        if plaintext_contest is not None: 
            plaintext_contests.append(plaintext_contest)
        else:
            log_warning(f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}")

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)
