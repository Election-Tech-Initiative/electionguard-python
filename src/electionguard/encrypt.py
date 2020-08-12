from typing import List, Optional
from uuid import getnode

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
    make_ciphertext_ballot_contest,
    make_ciphertext_ballot_selection,
    make_ciphertext_ballot,
)

from .election import (
    CiphertextElectionContext,
    InternalElectionDescription,
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .elgamal import elgamal_encrypt
from .group import ElementModP, ElementModQ, rand_q
from .logs import log_warning
from .nonces import Nonces
from .serializable import Serializable
from .tracker import get_hash_for_device
from .utils import get_optional, get_or_else_optional_func


class EncryptionDevice(Serializable):
    """
    Metadata for encryption device
    """

    uuid: int
    location: str

    def __init__(self, location: str) -> None:
        self.uuid = generate_device_uuid()
        self.location = location

    def get_hash(self) -> ElementModQ:
        """
        Get hash for encryption device
        :return: Starting hash
        """
        return get_hash_for_device(self.uuid, self.location)


class EncryptionMediator(object):
    """
    An object for caching election and encryption state.

    It composes Elections and Ballots.
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext
    _seed_hash: ElementModQ

    def __init__(
        self,
        election_metadata: InternalElectionDescription,
        context: CiphertextElectionContext,
        encryption_device: EncryptionDevice,
    ):
        self._metadata = election_metadata
        self._encryption = context
        self._seed_hash = encryption_device.get_hash()

    def encrypt(self, ballot: PlaintextBallot) -> Optional[CiphertextBallot]:
        """
        Encrypt the specified ballot using the cached election context.
        """
        encrypted_ballot = encrypt_ballot(
            ballot, self._metadata, self._encryption, self._seed_hash
        )
        if encrypted_ballot is not None and encrypted_ballot.tracking_hash is not None:
            self._seed_hash = encrypted_ballot.tracking_hash
        return encrypted_ballot


def generate_device_uuid() -> int:
    """
    Get unique identifier for device
    :return: Unique identifier
    """
    return getnode()


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
        description.object_id,
        vote=str(is_affirmative),
        is_placeholder_selection=is_placeholder,
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
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ,
    is_placeholder: bool = False,
    should_verify_proofs: bool = True,
) -> Optional[CiphertextBallotSelection]:
    """
    Encrypt a specific `BallotSelection` in the context of a specific `BallotContest`

    :param selection: the selection in the valid input form
    :param selection_description: the `SelectionDescription` from the `ContestDescription` which defines this selection's structure
    :param elgamal_public_key: the public key (K) used to encrypt the ballot
    :param crypto_extended_base_hash: the extended base hash of the election
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
    selection_nonce = nonce_sequence[selection_description.sequence_order]
    disjunctive_chaum_pedersen_nonce = next(iter(nonce_sequence))

    selection_representation = selection.to_int()

    # Generate the encryption
    elgamal_encryption = elgamal_encrypt(
        selection_representation, selection_nonce, elgamal_public_key
    )

    if elgamal_encryption is None:
        # will have logged about the failure earlier, so no need to log anything here
        return None

    # TODO: ISSUE #35: encrypt/decrypt: encrypt the extended_data field

    # Create the return object
    encrypted_selection = make_ciphertext_ballot_selection(
        object_id=selection.object_id,
        description_hash=selection_description_hash,
        ciphertext=get_optional(elgamal_encryption),
        elgamal_public_key=elgamal_public_key,
        crypto_extended_base_hash=crypto_extended_base_hash,
        proof_seed=disjunctive_chaum_pedersen_nonce,
        selection_representation=selection_representation,
        is_placeholder_selection=is_placeholder,
        nonce=selection_nonce,
    )

    if encrypted_selection.proof is None:
        return None  # log will have happened earlier

    # optionally, skip the verification step
    if not should_verify_proofs:
        return encrypted_selection

    # verify the selection.
    if encrypted_selection.is_valid_encryption(
        selection_description_hash, elgamal_public_key, crypto_extended_base_hash
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
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ,
    should_verify_proofs: bool = True,
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
    :param crypto_extended_base_hash: the extended base hash of the election
    :param nonce_seed: an `ElementModQ` used as a header to seed the `Nonce` generated for this contest.
                 this value can be (or derived from) the Ballot nonce, but no relationship is required
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default True)
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

    if not contest_description.is_valid():
        log_warning(f"malformed contest description: {contest_description}")
        return None

    # account for sequence id
    contest_description_hash = contest_description.crypto_hash()
    nonce_sequence = Nonces(contest_description_hash, nonce_seed)
    contest_nonce = nonce_sequence[contest_description.sequence_order]
    chaum_pedersen_nonce = next(iter(nonce_sequence))

    encrypted_selections: List[CiphertextBallotSelection] = list()

    selection_count = 0

    # TODO: ISSUE #54 this code could be inefficient if we had a contest
    # with a lot of choices, although the O(n^2) iteration here is small
    # compared to the huge cost of doing the cryptography.

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
                    selection,
                    description,
                    elgamal_public_key,
                    crypto_extended_base_hash,
                    contest_nonce,
                )
                break

        if not has_selection:
            # No selection was made for this possible value
            # so we explicitly set it to false
            encrypted_selection = encrypt_selection(
                selection_from(description),
                description,
                elgamal_public_key,
                crypto_extended_base_hash,
                contest_nonce,
            )

        if encrypted_selection is None:
            return None  # log will have happened earlier
        encrypted_selections.append(get_optional(encrypted_selection))

    # Handle Placeholder selections
    # After we loop through all of the real selections on the ballot,
    # we loop through each placeholder value and determine if it should be filled in

    # Add a placeholder selection for each possible seat in the contest
    for placeholder in contest_description.placeholder_selections:
        # for undervotes, select the placeholder value as true for each available seat
        # note this pattern is used since DisjunctiveChaumPedersen expects a 0 or 1
        # so each seat can only have a maximum value of 1 in the current implementation
        select_placeholder = False
        if selection_count < contest_description.number_elected:
            select_placeholder = True
            selection_count += 1

        encrypted_selection = encrypt_selection(
            selection=selection_from(
                description=placeholder,
                is_placeholder=True,
                is_affirmative=select_placeholder,
            ),
            selection_description=placeholder,
            elgamal_public_key=elgamal_public_key,
            crypto_extended_base_hash=crypto_extended_base_hash,
            nonce_seed=contest_nonce,
            is_placeholder=True,
            should_verify_proofs=True,
        )
        if encrypted_selection is None:
            return None  # log will have happened earlier
        encrypted_selections.append(get_optional(encrypted_selection))

    # TODO: ISSUE #33: support other cases such as cumulative voting
    # (individual selections being an encryption of > 1)
    if (
        contest_description.votes_allowed is not None
        and selection_count < contest_description.votes_allowed
    ):
        log_warning(
            "mismatching selection count: only n-of-m style elections are currently supported"
        )

    # Create the return object
    encrypted_contest = make_ciphertext_ballot_contest(
        object_id=contest.object_id,
        description_hash=contest_description_hash,
        ballot_selections=encrypted_selections,
        elgamal_public_key=elgamal_public_key,
        crypto_extended_base_hash=crypto_extended_base_hash,
        proof_seed=chaum_pedersen_nonce,
        number_elected=contest_description.number_elected,
        nonce=contest_nonce,
    )

    if encrypted_contest is None or encrypted_contest.proof is None:
        return None  # log will have happened earlier

    if not should_verify_proofs:
        return encrypted_contest

    # Verify the proof
    if encrypted_contest.is_valid_encryption(
        contest_description_hash, elgamal_public_key, crypto_extended_base_hash
    ):
        return encrypted_contest
    else:
        log_warning(
            f"mismatching contest proof for contest {encrypted_contest.object_id}"
        )
        return None


# TODO: ISSUE #57: add the device hash to the function interface so it can be propagated with the ballot.
# also propagate the seed hash so that the ballot tracking id's can be regenerated
# by traversing the collection of ballots encrypted by a specific device


def encrypt_ballot(
    ballot: PlaintextBallot,
    election_metadata: InternalElectionDescription,
    context: CiphertextElectionContext,
    seed_hash: ElementModQ,
    nonce: Optional[ElementModQ] = None,
    should_verify_proofs: bool = True,
) -> Optional[CiphertextBallot]:
    """
    Encrypt a specific `Ballot` in the context of a specific `CiphertextElectionContext`.

    This method accepts a ballot representation that only includes `True` selections.
    It will fill missing selections for a contest with `False` values, and generate `placeholder`
    selections to represent the number of seats available for a given contest.

    This method also allows for ballots to exclude passing contests for which the voter made no selections.
    It will fill missing contests with `False` selections and generate `placeholder` selections that are marked `True`.

    :param ballot: the ballot in the valid input form
    :param election_metadata: the `InternalElectionDescription` which defines this ballot's structure
    :param context: all the cryptographic context for the election
    :param seed_hash: Hash from previous ballot or starting hash from device
    :param nonce: an optional `int` used to seed the `Nonce` generated for this contest
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
    random_master_nonce = get_or_else_optional_func(nonce, lambda: rand_q())

    # Include a representation of the election and the external Id in the nonce's used
    # to derive other nonce values on the ballot
    nonce_seed = CiphertextBallot.nonce_seed(
        election_metadata.description_hash, ballot.object_id, random_master_nonce,
    )

    encrypted_contests: List[CiphertextBallotContest] = list()

    # only iterate on contests for this specific ballot style
    for description in election_metadata.get_contests_for(ballot.ballot_style):
        use_contest = None
        for contest in ballot.contests:
            if contest.object_id == description.object_id:
                use_contest = contest
                break
        # no selections provided for the contest, so create a placeholder contest
        if not use_contest:
            use_contest = contest_from(description)

        encrypted_contest = encrypt_contest(
            use_contest,
            description,
            context.elgamal_public_key,
            context.crypto_extended_base_hash,
            nonce_seed,
        )

        if encrypted_contest is None:
            return None  # log will have happened earlier
        encrypted_contests.append(get_optional(encrypted_contest))

    # Create the return object
    encrypted_ballot = make_ciphertext_ballot(
        ballot.object_id,
        ballot.ballot_style,
        election_metadata.description_hash,
        seed_hash,
        encrypted_contests,
        random_master_nonce,
    )

    if not encrypted_ballot.tracking_hash:
        return None

    if not should_verify_proofs:
        return encrypted_ballot

    # Verify the proofs
    if encrypted_ballot.is_valid_encryption(
        election_metadata.description_hash,
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        return encrypted_ballot
    else:
        return None  # log will have happened earlier
