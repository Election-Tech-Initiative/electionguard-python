from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)
from .chaum_pedersen import ChaumPedersenDecryptionProof, make_chaum_pedersen_generic
from .dlog import discrete_log
from .election import (
    InternalElectionDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .elgamal import ElGamalKeyPair, ElGamalCiphertext
from .group import (
    ElementModP,
    ElementModQ,
    rand_q,
    pow_p,
    mult_p,
    mult_inv_p,
    int_to_p_unchecked,
    G,
)
from .logs import log_warning
from .nonces import Nonces
from .serializable import Serializable
from .utils import get_optional

ELECTION_PUBLIC_KEY = ElementModP

# The Methods in this file can be used to decrypt values if private keys or nonces are known


def ciphertext_ballot_to_dict(
    cballot: CiphertextBallot,
) -> Dict[str, ElGamalCiphertext]:
    """
    Given a `CiphertextBallot`, constructs a dict from selection object_ids to the corresponding
    ciphertexts.
    """
    result: Dict[str, ElGamalCiphertext] = {}
    for c in cballot.contests:
        for s in c.ballot_selections:
            if not s.is_placeholder_selection:
                result[s.object_id] = s.ciphertext
    return result


def plaintext_ballot_to_dict(pballot: PlaintextBallot) -> Dict[str, int]:
    """
    Given a `PlaintextBallot`, constructs a dict from selection object_ids to the corresponding
    plaintext integer value.
    """
    result: Dict[str, int] = {}
    for c in pballot.contests:
        for s in c.ballot_selections:
            if not s.is_placeholder_selection:
                result[s.object_id] = s.to_int()
    return result


def decrypt_ciphertext_with_proof(
    ciphertext: ElGamalCiphertext,
    keypair: ElGamalKeyPair,
    seed: Optional[ElementModQ] = None,
    hash_header: Optional[ElementModQ] = None,
) -> Tuple[int, ChaumPedersenDecryptionProof]:
    """
    Decrypts an ElGamal ciphertext, returning both the plaintext as well as a Chaum-Pedersen proof
    that proves the decryption coresponds to the ciphertext.
    :param ciphertext: Any ElGamal ciphertext
    :param keypair: The public / secret key pair used for the election.
    :param seed: Used to randomize the generation of the Chaum-Pedersen proof. If None, generated at random internally.
    :param hash_header: A value used when generating the challenge, usually the election extended base hash (𝑄').
    :return: a tuple of the plaintext and the proof
    """

    # Ciphertext:
    #     pad = g ^ nonce
    #     data = (g ^ plaintext) * public_key ^ nonce
    #          = (g ^ plaintext) * (g^secret_key) ^ nonce
    #          = (g ^ {plaintext + secret_key * nonce} )

    # We can also define:
    #     blinder = data / { g ^ plaintext }
    #             = g ^ { secret_key * nonce }

    # And, then we want to generate a Chaum-Pedersen proof that (g, public_key), (pad, blinder) have
    # a shared exponent (the secret).

    if seed is None:
        seed = rand_q()

    blinder = pow_p(ciphertext.pad, keypair.secret_key)
    g_exp_plaintext = mult_p(ciphertext.data, mult_inv_p(blinder))
    plaintext = discrete_log(g_exp_plaintext)

    proof = make_chaum_pedersen_generic(
        int_to_p_unchecked(G), ciphertext.pad, keypair.secret_key, seed, hash_header
    )
    return plaintext, ChaumPedersenDecryptionProof(proof)


def decrypt_selection_with_secret_and_proof(
    selection: CiphertextBallotSelection,
    description: SelectionDescription,
    public_key: ElementModP,
    secret_key: ElementModQ,
    crypto_extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
) -> Tuple[Optional[PlaintextBallotSelection], Optional[ChaumPedersenDecryptionProof]]:
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
        return None, None

    keypair = ElGamalKeyPair(secret_key, public_key)
    plaintext_vote, proof = decrypt_ciphertext_with_proof(
        selection.ciphertext, keypair, hash_header=crypto_extended_base_hash
    )

    plaintext_selection = PlaintextBallotSelection(
        selection.object_id,
        f"{bool(plaintext_vote)}",
        selection.is_placeholder_selection,
    )

    return plaintext_selection, proof


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
        f"{bool(plaintext_vote)}",
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
        f"{bool(plaintext_vote)}",
        selection.is_placeholder_selection,
    )


def decrypt_contest_with_secret_and_proofs(
    contest: CiphertextBallotContest,
    description: ContestDescriptionWithPlaceholders,
    public_key: ElementModP,
    secret_key: ElementModQ,
    crypto_extended_base_hash: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Tuple[
    Optional[PlaintextBallotContest], Optional[Dict[str, ChaumPedersenDecryptionProof]]
]:
    """
    Decrypt the specified `CiphertextBallotContest` within the context of the specified contest.

    :param contest: the contest to decrypt
    :param description: the qualified contest metadata that includes placeholder selections
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    :return: the plaintext contest plus a dictionary mapping from selection object_id's to their decryption proofs
    """

    if not suppress_validity_check and not contest.is_valid_encryption(
        description.crypto_hash(), public_key, crypto_extended_base_hash
    ):
        return None, None

    plaintext_selections: List[PlaintextBallotSelection] = list()
    selection_proofs: Dict[str, ChaumPedersenDecryptionProof] = {}

    for selection in contest.ballot_selections:
        selection_description = description.selection_for(selection.object_id)
        plaintext_selection, proof = decrypt_selection_with_secret_and_proof(
            selection,
            get_optional(selection_description),
            public_key,
            secret_key,
            crypto_extended_base_hash,
            suppress_validity_check,
        )
        if plaintext_selection is not None and proof is not None:
            if (
                not remove_placeholders
                or not plaintext_selection.is_placeholder_selection
            ):
                plaintext_selections.append(plaintext_selection)
                selection_proofs[selection.object_id] = proof
        else:
            log_warning(
                f"decryption with secret failed for contest: {contest.object_id} selection: {selection.object_id}"
            )
            return None, None

    return (
        PlaintextBallotContest(contest.object_id, plaintext_selections),
        selection_proofs,
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


@dataclass
class ProvenPlaintextBallot(Serializable):
    """
    When decrypting a ballot with proofs, the result is an instance of this class.
    """

    ballot: PlaintextBallot
    """
    The decrypted ballot.
    """

    proofs: Dict[str, ChaumPedersenDecryptionProof]
    """
    A dictionary mapping from selection object_ids to the corresponding Chaum-Pedersen proof of its correct decryption.
    """


def decrypt_ballot_with_secret_and_proofs(
    ballot: CiphertextBallot,
    election_metadata: InternalElectionDescription,
    crypto_extended_base_hash: ElementModQ,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[ProvenPlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    :return: the plaintext ballot plus a dictionary mapping from selection object_id's to their decryption proofs
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        election_metadata.description_hash, public_key, crypto_extended_base_hash
    ):
        return None

    plaintext_contests: List[PlaintextBallotContest] = list()
    selection_proofs: Dict[str, ChaumPedersenDecryptionProof] = {}

    for contest in ballot.contests:
        description = election_metadata.contest_for(contest.object_id)
        plaintext_contest, proofs = decrypt_contest_with_secret_and_proofs(
            contest,
            get_optional(description),
            public_key,
            secret_key,
            crypto_extended_base_hash,
            suppress_validity_check,
            remove_placeholders,
        )
        if plaintext_contest is not None and proofs is not None:
            plaintext_contests.append(plaintext_contest)
            selection_proofs.update(proofs)
        else:
            log_warning(
                f"decryption with nonce failed for ballot: {ballot.object_id} selection: {contest.object_id}"
            )
            return None

    return ProvenPlaintextBallot(
        PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests),
        selection_proofs,
    )


def decrypt_ballot_with_secret(
    ballot: CiphertextBallot,
    election_metadata: InternalElectionDescription,
    crypto_extended_base_hash: ElementModQ,
    public_key: ElementModP,
    secret_key: ElementModQ,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param secret_key: the known secret key used to generate the public key for this election
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        election_metadata.description_hash, public_key, crypto_extended_base_hash
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

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)


def decrypt_ballot_with_nonce(
    ballot: CiphertextBallot,
    election_metadata: InternalElectionDescription,
    crypto_extended_base_hash: ElementModQ,
    public_key: ElementModP,
    nonce: Optional[ElementModQ] = None,
    suppress_validity_check: bool = False,
    remove_placeholders: bool = True,
) -> Optional[PlaintextBallot]:
    """
    Decrypt the specified `CiphertextBallot` within the context of the specified election.

    :param ballot: the ballot to decrypt
    :param election_metadata: the qualified election metadata that includes placeholder selections
    :param crypto_extended_base_hash: the extended base hash code (𝑄') for the election
    :param public_key: the public key for the election (K)
    :param nonce: the optional master ballot nonce that was either seeded to, or gernated by the encryption function
    :param suppress_validity_check: do not validate the encryption prior to decrypting (useful for tests)
    :param remove_placeholders: filter out placeholder ciphertext selections after decryption
    """

    if not suppress_validity_check and not ballot.is_valid_encryption(
        election_metadata.description_hash, public_key, crypto_extended_base_hash
    ):
        return None

    # Use the hashed representation included in the ballot
    # or override with the provided values
    if nonce is None:
        nonce_seed = ballot.hashed_ballot_nonce()
    else:
        nonce_seed = CiphertextBallot.nonce_seed(
            election_metadata.description_hash, ballot.object_id, nonce
        )

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

    return PlaintextBallot(ballot.object_id, ballot.ballot_style, plaintext_contests)
