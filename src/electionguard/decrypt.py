from typing import Optional, List

from .ballot import (
    CyphertextBallot,
    CyphertextBallotContest,
    CyphertextBallotSelection,
    PlaintextBallot, 
    PlaintextBallotContest, 
    PlaintextBallotSelection,
)

from .election import (
    CyphertextElection, 
    ElectionDescription, 
    InternalElectionDescription,
    ContestDescriptionWithPlaceholders, 
    SelectionDescription
)

from .elgamal import ElGamalCiphertext
from .group import Q, ElementModP, ElementModQ, unwrap_optional

from .logs import log_warning

def decrypt_selection_with_secret(
    selection: CyphertextBallotSelection, 
    description: SelectionDescription,
    public_key: ElementModP, 
    secret_key: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotSelection]:
    
    if not suppress_validity_check and not selection.is_valid_encryption(description.crypto_hash(), public_key):
            return None

    plaintext = selection.message.decrypt(secret_key)

    # TODO: handle decryption of the extradata field if needed

    return PlaintextBallotSelection(selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection)

def decrypt_selection_with_nonce(
    selection: CyphertextBallotSelection, 
    description: SelectionDescription,
    public_key: ElementModP,
    nonce: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotSelection]:
    
    if not suppress_validity_check and not selection.is_valid_encryption(description.crypto_hash(), public_key):
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
    nonce: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotContest]:

    if not suppress_validity_check and not contest.is_valid_encryption(description.crypto_hash(), public_key):
        return None
    
    plaintext_selections: List[PlaintextBallotSelection] = list()
    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection = decrypt_selection_with_nonce(
                selection, 
                unwrap_optional(selection_description), 
                public_key, 
                selection.nonce, 
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
    nonce: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallot]:

    if not suppress_validity_check and not ballot.is_valid_encryption(extended_base_hash, public_key):
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest = decrypt_contest_with_nonce(
            contest,
            unwrap_optional(description),
            public_key,
            nonce,
            suppress_validity_check
        )
        if plaintext_contest is not None: 
            plaintext_contests.append(plaintext_contest)
        else:
            log_warning(f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}")

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)
