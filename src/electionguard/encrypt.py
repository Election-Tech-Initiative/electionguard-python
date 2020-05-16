from typing import Optional, List
from secrets import randbelow

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)

from .election import (
    CiphertextElection,
    InternalElectionDescription,
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .elgamal import elgamal_encrypt
from .group import Q, ElementModP, ElementModQ, int_to_q
from .hash import hash_elems
from .logs import log_warning, log_debug
from .nonces import Nonces
from .utils import unwrap_optional


class EncryptionCompositor(object):
    """
    EncryptionCompositor is an object for caching election and encryption state.

    It composes Elections and Ballots.
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElection

    def __init__(
        self,
        election_metadata: InternalElectionDescription,
        encryption_context: CiphertextElection,
    ):
        self._metadata = election_metadata
        self._encryption = encryption_context

    def encrypt(self, ballot: PlaintextBallot) -> Optional[CiphertextBallot]:
        """
        Encrypt the specified ballot using the cached election context.
        """
        return encrypt_ballot(ballot, self._metadata, self._encryption)


# TODO: most of the functions here could be represented as methods on their corresponding classes,
#   although I like having all of the encryption-related stuff in one place. For now, I'm going to
#   go add helper methods on those classes that just call these.


def selection_from(
    description: SelectionDescription,
    is_placeholder: bool = False,
    is_affirmative: bool = False,
) -> PlaintextBallotSelection:
    """
    Construct a `BallotSelection` from a specific `SelectionDescription`.
    This function is useful for filling selections when a voter undervotes a ballot.
    It is also used to create placeholder representations when generating the `ConstantChaumPedersenProof`

    :param description: The `SelectionDescription` which provides the relevant `object_id`
    :param is_placeholder: Mark this selection as a placeholder value
    :param is_affirmative: Mark this selection as `yes`
    :return: A BallotSelection
    """
    return PlaintextBallotSelection(
        description.object_id, str(is_affirmative), is_placeholder
    )


def contest_from(description: ContestDescription) -> PlaintextBallotContest:
    """
    Construct a `BallotContest` from a specific `ContestDescription` with all false fields.
    This function is useful for filling contests and selections when a voter undervotes a ballot.

    :param description: The `ContestDescription` used to derive the well-formed `BallotContest`
    :return: a `BallotContest`
    """
    selections: List[PlaintextBallotSelection] = list()

    for selection_description in description.ballot_selections:
        selections.append(selection_from(selection_description))

    return PlaintextBallotContest(description.object_id, selections)


def encrypt_selection(
    selection: PlaintextBallotSelection,
    selection_description: SelectionDescription,
    elgamal_public_key: ElementModP,
    nonce_seed: ElementModQ,
    is_placeholder: bool = False,
    should_verify_proofs: bool = True,
) -> Optional[CiphertextBallotSelection]:
    """
    Encrypt a specific `BallotSelection` in the context of a specific `BallotContest`

    :param selection: the selection in the valid input form
    :param selection_description: the `SelectionDescription` from the `ContestDescription` which defines this selection's structure
    :param elgamal_public_key: the public key (K) used to encrypt the ballot
    :param nonce_seed: an `ElementModQ` used as a header to seed the `Nonce` generated for this selection.
                 this value can be (or derived from) the BallotContest nonce, but no relationship is required
    :param is_placeholder: specifies if this is a placeholder selection
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default True)
    """

    # Validate Input
    if not selection.is_valid(selection_description.object_id):
        log_warning(f"malformed input selection: {selection}")
        return None

    selection_description_hash = selection_description.crypto_hash()
    nonce_sequence = Nonces(selection_description_hash, nonce_seed)
    (selection_nonce, chaum_pedersen_nonce) = nonce_sequence[0:2]

    selection_representation = selection.to_int()

    # Generate the encryption
    elgamal_encryption = elgamal_encrypt(
        selection_representation, selection_nonce, elgamal_public_key
    )

    # Create the return object
    encrypted_selection = CiphertextBallotSelection(
        object_id=selection.object_id,
        description_hash=selection_description_hash,
        message=unwrap_optional(elgamal_encryption),
        elgamal_public_key=elgamal_public_key,
        proof_seed=chaum_pedersen_nonce,
        selection_representation=selection_representation,
        is_placeholder_selection=is_placeholder,
        nonce=selection_nonce,
    )

    assert encrypted_selection.proof is not None

    # optionally, skip the verification step
    if not should_verify_proofs:
        return encrypted_selection

    # verify the selection.
    if encrypted_selection.is_valid_encryption(
        selection_description_hash, elgamal_public_key
    ):
        return encrypted_selection
    else:
        log_warning(
            f"mismatching selection proof for selection {encrypted_selection.object_id}"
        )
        return None


def encrypt_contest(
    contest: PlaintextBallotContest,
    contest_description: ContestDescriptionWithPlaceholders,
    elgamal_public_key: ElementModP,
    nonce_seed: ElementModQ,
    should_verify_proofs: bool = True,
    elgamal_private_key_debug: Optional[ElementModQ] = None,
) -> Optional[CiphertextBallotContest]:

    """
    Encrypt a specific `BallotContest` in the context of a specific `Ballot`.

    This method accepts a contest representation that only includes `True` selections.
    It will fill missing selections for a contest with `False` values, and generate `placeholder`
    selections to represent the number of seats available for a given contest.  By adding `placeholder`
    votes

    :param contest: the contest in the valid input form
    :param contest_description: the `ContestDescriptionWithPlaceholders` from the `ContestDescription` which defines this contest's structure
    :param elgamal_public_key: the public key (k) used to encrypt the ballot
    :param nonce_seed: an `ElementModQ` used as a header to seed the `Nonce` generated for this contest.
                 this value can be (or derived from) the Ballot nonce, but no relationship is required
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default True)
    :param elgamal_private_key_debug: if not None, this private key will be used to log useful debugging info about the ciphertexts
    """

    # Validate Input
    if not contest.is_valid(
        contest_description.object_id,
        len(contest_description.ballot_selections),
        contest_description.number_elected,
        contest_description.votes_allowed,
    ):
        log_warning(f"malformed input contest: {contest}")
        return None

    # TODO: check the hash of the description matches the expected contest description hash?
    # is it possible one could attack this function by passing in a description with values added or eremoved?

    if not contest_description.is_valid():
        log_warning(f"malformed contest description: {contest_description}")
        return None

    # account for sequence id
    contest_description_hash = contest_description.crypto_hash()
    nonce_sequence = Nonces(contest_description_hash, nonce_seed)
    (contest_nonce, chaum_pedersen_nonce) = nonce_sequence[0:2]

    encrypted_selections: List[CiphertextBallotSelection] = list()

    selection_count = 0

    # TODO: this code could be inefficient if we had a contest with a lot of choices, although the
    #  O(n^2) iteration here is peanuts compared to the huge cost of doing the cryptography.

    # Generate the encrypted selections
    for description in contest_description.ballot_selections:
        has_selection = False
        encrypted_selection = None

        # iterate over the actual selections for each contest description
        # and apply the selected value if it exists.  If it does not, an explicit
        # false is entered instead and the selection_count is not incremented
        # this allows consumers to only pass in the relevant selections made by a voter
        for selection in contest.ballot_selections:
            if selection.object_id == description.object_id:
                # track the selection count so we can append the
                # appropriate number of true placeholder votes
                has_selection = True
                selection_count += selection.to_int()
                encrypted_selection = encrypt_selection(
                    selection, description, elgamal_public_key, contest_nonce
                )
        if not has_selection:
            # No selection was made for this possible value
            # so we explicitly set it to false
            encrypted_selection = encrypt_selection(
                selection_from(description),
                description,
                elgamal_public_key,
                contest_nonce,
            )
        assert encrypted_selection is not None
        encrypted_selections.append(unwrap_optional(encrypted_selection))

    # Handle Placeholder selections
    # After we loop through all of the real selections on the ballot,
    # we loop through each placeholder value and determine if it should be filled in

    # Add a placeholder selection for each possible seat in the contest
    for placeholder in contest_description.placeholder_selections:
        # for undervotes, select the placeholder value as true for each available seat
        # note this pattern is used since DisjuctiveChaumPedersen expects a 0 or 1
        # so each seat can only have a maximum value of 1 in the current implementation
        select_placeholder = False
        if selection_count < contest_description.number_elected:
            select_placeholder = True
            selection_count += 1

        encrypted_selection = encrypt_selection(
            selection_from(
                description=placeholder,
                is_placeholder=True,
                is_affirmative=select_placeholder,
            ),
            placeholder,
            elgamal_public_key,
            contest_nonce,
        )
        encrypted_selections.append(unwrap_optional(encrypted_selection))

    # TODO: support other cases such as cumulative voting (individual selections being an encryption of > 1)
    if selection_count < contest_description.votes_allowed:
        log_warning(
            "mismatching selection count: only n-of-m style elections are currently supported"
        )
        pass

    # Create the return object
    encrypted_contest = CiphertextBallotContest(
        object_id=contest.object_id,
        description_hash=contest_description_hash,
        ballot_selections=encrypted_selections,
        elgamal_public_key=elgamal_public_key,
        proof_seed=chaum_pedersen_nonce,
        number_elected=contest_description.number_elected,
        nonce=contest_nonce,
    )

    if elgamal_private_key_debug is not None:
        log_debug(
            f"Decrypted selections (should be {contest_description.number_elected} of {contest_description.votes_allowed}):"
        )
        for s in encrypted_selections:
            log_debug(
                f"ObjectID: {s.object_id}, decrypted: {s.message.decrypt(elgamal_private_key_debug)}"
            )

    assert encrypted_contest is not None
    assert encrypted_contest.proof is not None

    if not should_verify_proofs:
        return encrypted_contest

    # Verify the proof
    if encrypted_contest.is_valid_encryption(
        contest_description_hash, elgamal_public_key
    ):
        return encrypted_contest
    else:
        log_warning(
            f"mismatching contest proof for contest {encrypted_contest.object_id}"
        )
        return None


def encrypt_ballot(
    ballot: PlaintextBallot,
    election_metadata: InternalElectionDescription,
    encryption_context: CiphertextElection,
    nonce: Optional[ElementModQ] = None,
    should_verify_proofs: bool = True,
) -> Optional[CiphertextBallot]:
    """
    Encrypt a specific `Ballot` in the context of a specific `CiphertextElection`.

    This method accepts a ballot representation that only includes `True` selections.
    It will fill missing selections for a contest with `False` values, and generate `placeholder`
    selections to represent the number of seats available for a given contest.  By adding `placeholder`
    votes

    This method also allows for ballots to exclude passing contests for which the voter made no selections.
    It will fill missing contests with `False` selections and generate `placeholder` selections that are marked `True`

    :param ballot: the ballot in the valid input form
    :param election_metadata: the `InternalElectionDescription` which defines this ballot's structure
    :param elgamal_public_key: the public key (K) used to encrypt the ballot
    :param nonce: an optional `int` used to seed the `Nonce` generated for this contest.
                 if this value is not provided, the secret generating mechanism of the OS provides its own
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default True)
    """

    # Determine the relevant range of contests for this ballot style
    style = election_metadata.get_ballot_style(ballot.ballot_style)

    # Validate Input
    if not ballot.is_valid(style.object_id):
        log_warning(f"malformed input ballot: {ballot}")
        return None

    # Generate a random master nonce to use for the contest and selection nonce's on the ballot
    if nonce is None:
        random_master_nonce = unwrap_optional(int_to_q(randbelow(Q)))
    else:
        random_master_nonce = unwrap_optional(nonce)

    # Include a representation of the election and the external Id in the nonce's used
    # to derive other nonce values on the ballot
    nonce_seed = hash_elems(
        encryption_context.crypto_extended_base_hash,
        ballot.object_id,
        random_master_nonce,
    )

    encrypted_contests: List[CiphertextBallotContest] = list()

    # only iterate on contests for this specific ballot style
    for description in election_metadata.get_contests_for(ballot.ballot_style):
        for contest in ballot.contests:
            # encrypt it as specified
            if contest.object_id == description.object_id:
                encrypted_contest = encrypt_contest(
                    contest,
                    description,
                    encryption_context.elgamal_public_key,
                    nonce_seed,
                )
            else:
                # the contest was not voted on this ballot,
                # but we still need to encrypt selections for it
                encrypted_contest = encrypt_contest(
                    contest_from(description),
                    description,
                    encryption_context.elgamal_public_key,
                    nonce_seed,
                )
            encrypted_contests.append(unwrap_optional(encrypted_contest))

    # Create the return object
    encrypted_ballot = CiphertextBallot(
        ballot.object_id,
        ballot.ballot_style,
        encryption_context.crypto_extended_base_hash,
        encrypted_contests,
        random_master_nonce,
    )

    if not should_verify_proofs:
        return encrypted_ballot

    # Verify the proofs
    if encrypted_ballot.is_valid_encryption(
        encryption_context.crypto_extended_base_hash,
        encryption_context.elgamal_public_key,
    ):
        return encrypted_ballot
    else:
        return None
