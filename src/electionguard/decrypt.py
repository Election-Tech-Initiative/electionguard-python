from typing import Optional, List

from .ballot import (
    CyphertextBallot,
    CyphertextBallotContest,
    CyphertextBallotSelection,
    PlaintextBallot, 
    PlaintextBallotContest, 
    PlaintextBallotSelection,
)

from .election import CyphertextElection, Election, ContestDescription, SelectionDescription

from .elgamal import ElGamalCiphertext
from .group import Q, ElementModP, ElementModQ

def decrypt_selection_with_secret(
    selection: CyphertextBallotSelection, 
    description: SelectionDescription,
    public_key: ElementModP, 
    secret_key: ElementModQ,
    suppress_validity_check: bool = False) -> Optional[PlaintextBallotSelection]:
    
    if not suppress_validity_check and not selection.is_valid_encryption(description.crypto_hash(), public_key):
            return None

    plaintext = selection.message.decrypt(secret_key)

    # TODO: handle decryption of the extradata field ifg needed

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

    # TODO: handle decryption of the extradata field ifg needed

    return PlaintextBallotSelection(selection.object_id, f"{bool(plaintext)}", selection.is_placeholder_selection)