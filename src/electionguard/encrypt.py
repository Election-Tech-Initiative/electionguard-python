from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Type, TypeVar
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

from .ballot_code import get_hash_for_device
from .election import CiphertextElectionContext
from .elgamal import ElGamalPublicKey, elgamal_encrypt, hashed_elgamal_encrypt
from .serialize import padded_decode, padded_encode
from .group import ElementModQ, rand_q
from .logs import log_info, log_warning
from .manifest import (
    InternalManifest,
    ContestDescription,
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .nonces import Nonces
from .type import SelectionId
from .utils import (
    ContestException,
    NullVoteException,
    OverVoteException,
    UnderVoteException,
    get_optional,
    get_or_else_optional_func,
    ContestErrorType,
)


_T = TypeVar("_T", bound="ContestData")


@dataclass
class ContestData:
    """Contests errors and extended data from the selections on the contest."""

    error: Optional[ContestErrorType] = field(default=None)
    error_data: Optional[List[SelectionId]] = field(default=None)
    write_ins: Optional[Dict[SelectionId, str]] = field(default=None)

    @classmethod
    def from_bytes(cls: Type[_T], data: bytes) -> _T:
        return padded_decode(cls, data)

    def to_bytes(self) -> bytes:
        return padded_encode(self)


@dataclass
class EncryptionDevice:
    """
    Metadata for encryption device
    """

    device_id: int
    """Unique identifier for device"""

    session_id: int
    """Used to identify session and protect the timestamp"""

    launch_code: int
    """Election initialization value"""

    location: str
    """Arbitrary string to designate the location of device"""

    def get_hash(self) -> ElementModQ:
        """
        Get hash for encryption device
        :return: Starting hash
        """
        return get_hash_for_device(
            self.device_id, self.session_id, self.launch_code, self.location
        )

    # pylint: disable=no-self-use
    def get_timestamp(self) -> int:
        """
        Get the current timestamp in utc
        """
        return int(datetime.utcnow().timestamp())


class EncryptionMediator:
    """
    An object for caching election and encryption state.

    It composes Elections and Ballots.
    """

    _internal_manifest: InternalManifest
    _context: CiphertextElectionContext
    _encryption_seed: ElementModQ

    def __init__(
        self,
        internal_manifest: InternalManifest,
        context: CiphertextElectionContext,
        encryption_device: EncryptionDevice,
    ):
        self._internal_manifest = internal_manifest
        self._context = context
        self._encryption_seed = encryption_device.get_hash()

    def encrypt(self, ballot: PlaintextBallot) -> Optional[CiphertextBallot]:
        """
        Encrypt the specified ballot using the cached election context.
        """

        log_info(f" encrypt: objectId: {ballot.object_id}")
        encrypted_ballot = encrypt_ballot(
            ballot, self._internal_manifest, self._context, self._encryption_seed
        )
        if encrypted_ballot is not None and encrypted_ballot.code is not None:
            self._encryption_seed = encrypted_ballot.code
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
        1 if is_affirmative else 0,
        is_placeholder,
    )


def contest_from(description: ContestDescription) -> PlaintextBallotContest:
    """
    Construct a `BallotContest` from a specific `ContestDescription` with all false fields.
    This function is useful for filling contests and selections when a voter undervotes a ballot.

    :param description: The `ContestDescription` used to derive the well-formed `BallotContest`
    :return: a `BallotContest`
    """

    selections: List[PlaintextBallotSelection] = []

    for selection_description in description.ballot_selections:
        selections.append(selection_from(selection_description))

    return PlaintextBallotContest(description.object_id, selections)


def encrypt_selection(
    selection: PlaintextBallotSelection,
    selection_description: SelectionDescription,
    elgamal_public_key: ElGamalPublicKey,
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ,
    is_placeholder: bool = False,
    should_verify_proofs: bool = False,
) -> Optional[CiphertextBallotSelection]:
    """
    Encrypt a specific `BallotSelection` in the context of a specific `BallotContest`

    :param selection: the selection in the valid input form
    :param selection_description: the `SelectionDescription` from the
        `ContestDescription` which defines this selection's structure
    :param elgamal_public_key: the public key (K) used to encrypt the ballot
    :param crypto_extended_base_hash: the extended base hash of the election
    :param nonce_seed: an `ElementModQ` used as a header to seed the `Nonce` generated for this selection.
                 this value can be (or derived from) the BallotContest nonce, but no relationship is required
    :param is_placeholder: specifies if this is a placeholder selection
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default False)
    """

    # Validate Input
    if not selection.is_valid(selection_description.object_id):
        log_warning(f"malformed input selection: {selection}")
        return None

    selection_description_hash = selection_description.crypto_hash()
    nonce_sequence = Nonces(selection_description_hash, nonce_seed)
    selection_nonce = nonce_sequence[selection_description.sequence_order]
    disjunctive_chaum_pedersen_nonce = next(iter(nonce_sequence))

    log_info(
        f": encrypt_selection: for {selection_description.object_id} hash: {selection_description_hash.to_hex()}"
    )

    selection_representation = selection.vote

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
        selection.object_id,
        selection_description.sequence_order,
        selection_description_hash,
        get_optional(elgamal_encryption),
        elgamal_public_key,
        crypto_extended_base_hash,
        disjunctive_chaum_pedersen_nonce,
        selection_representation,
        is_placeholder,
        selection_nonce,
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
    log_warning(
        f"mismatching selection proof for selection {encrypted_selection.object_id}"
    )
    return None


def encrypt_contest(
    contest: PlaintextBallotContest,
    contest_description: ContestDescriptionWithPlaceholders,
    elgamal_public_key: ElGamalPublicKey,
    crypto_extended_base_hash: ElementModQ,
    nonce_seed: ElementModQ,
    should_verify_proofs: bool = False,
) -> Optional[CiphertextBallotContest]:
    """
    Encrypt a specific `BallotContest` in the context of a specific `Ballot`.

    This method accepts a contest representation that only includes `True` selections.
    It will fill missing selections for a contest with `False` values, and generate `placeholder`
    selections to represent the number of seats available for a given contest.  By adding `placeholder`
    votes

    :param contest: the contest in the valid input form
    :param contest_description: the `ContestDescriptionWithPlaceholders`
        from the `ContestDescription` which defines this contest's structure
    :param elgamal_public_key: the public key (k) used to encrypt the ballot
    :param crypto_extended_base_hash: the extended base hash of the election
    :param nonce_seed: an `ElementModQ` used as a header to seed the `Nonce` generated for this contest.
                 this value can be (or derived from) the Ballot nonce, but no relationship is required
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default False)
    """
    error: Optional[ContestErrorType] = None
    error_data: Optional[List[SelectionId]] = None

    # Validate Input
    try:
        contest.valid(contest_description)
    except OverVoteException as ove:
        error = ove.type
        error_data = ove.overvoted_ids
    except (NullVoteException, UnderVoteException) as nve:
        error = nve.type
    except ContestException as ce:
        log_warning(str(ce))
        return None

    # account for sequence id
    contest_description_hash = contest_description.crypto_hash()
    nonce_sequence = Nonces(contest_description_hash, nonce_seed)
    contest_nonce = nonce_sequence[contest_description.sequence_order]
    chaum_pedersen_nonce = next(iter(nonce_sequence))

    encrypted_selections: List[CiphertextBallotSelection] = []

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
            # If overvote, no votes should be counted and instead placeholders should be used.
            if (
                selection.object_id == description.object_id
                and error is not ContestErrorType.OverVote
            ):
                # track the selection count so we can append the
                # appropriate number of true placeholder votes
                has_selection = True
                selection_count += selection.vote
                encrypted_selection = encrypt_selection(
                    selection,
                    description,
                    elgamal_public_key,
                    crypto_extended_base_hash,
                    contest_nonce,
                    should_verify_proofs=should_verify_proofs,
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
                should_verify_proofs=should_verify_proofs,
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
            should_verify_proofs=should_verify_proofs,
        )
        if encrypted_selection is None:
            return None  # log will have happened earlier
        encrypted_selections.append(get_optional(encrypted_selection))

    encrypted_contest_data = hashed_elgamal_encrypt(
        ContestData(error, error_data, contest.write_ins).to_bytes(),
        Nonces(contest_nonce, "constant-extended-data")[0],
        elgamal_public_key,
        crypto_extended_base_hash,
    )

    # Create the return object
    encrypted_contest = make_ciphertext_ballot_contest(
        contest.object_id,
        contest_description.sequence_order,
        contest_description_hash,
        encrypted_selections,
        elgamal_public_key,
        crypto_extended_base_hash,
        chaum_pedersen_nonce,
        contest_description.number_elected,
        nonce=contest_nonce,
        extended_data=encrypted_contest_data,
    )

    if should_verify_proofs or not encrypted_contest.proof:
        if encrypted_contest.is_valid_encryption(
            contest_description_hash, elgamal_public_key, crypto_extended_base_hash
        ):
            return encrypted_contest
        log_warning(
            f"mismatching contest proof for contest {encrypted_contest.object_id}"
        )
        return None

    return encrypted_contest


# TODO: ISSUE #57: add the device hash to the function interface so it can be propagated with the ballot.
# also propagate the seed so that the ballot codes can be regenerated
# by traversing the collection of ballots encrypted by a specific device


def encrypt_ballot(
    ballot: PlaintextBallot,
    internal_manifest: InternalManifest,
    context: CiphertextElectionContext,
    encryption_seed: ElementModQ,
    nonce: Optional[ElementModQ] = None,
    should_verify_proofs: bool = False,
) -> Optional[CiphertextBallot]:
    """
    Encrypt a specific `Ballot` in the context of a specific `CiphertextElectionContext`.

    This method accepts a ballot representation that only includes `True` selections.
    It will fill missing selections for a contest with `False` values, and generate `placeholder`
    selections to represent the number of seats available for a given contest.

    This method also allows for ballots to exclude passing contests for which the voter made no selections.
    It will fill missing contests with `False` selections and generate `placeholder` selections that are marked `True`.

    :param ballot: the ballot in the valid input form
    :param internal_manifest: the `InternalManifest` which defines this ballot's structure
    :param context: all the cryptographic context for the election
    :param encryption_seed: Hash from previous ballot or starting hash from device
    :param nonce: an optional `int` used to seed the `Nonce` generated for this contest
                 if this value is not provided, the secret generating mechanism of the OS provides its own
    :param should_verify_proofs: specify if the proofs should be verified prior to returning (default False)
    """

    # Determine the relevant range of contests for this ballot style
    style = internal_manifest.get_ballot_style(ballot.style_id)

    # Validate Input
    if not ballot.is_valid(style.object_id):
        log_warning(f"malformed input ballot: {ballot}")
        return None

    # Generate a random master nonce to use for the contest and selection nonce's on the ballot
    random_master_nonce = get_or_else_optional_func(nonce, lambda: rand_q())

    # Include a representation of the election and the external Id in the nonce's used
    # to derive other nonce values on the ballot
    nonce_seed = CiphertextBallot.nonce_seed(
        internal_manifest.manifest_hash,
        ballot.object_id,
        random_master_nonce,
    )

    log_info(f": manifest_hash : {internal_manifest.manifest_hash.to_hex()}")
    log_info(f": encryption_seed : {encryption_seed.to_hex()}")

    encrypted_contests = encrypt_ballot_contests(
        ballot,
        internal_manifest,
        context,
        nonce_seed,
        should_verify_proofs=should_verify_proofs,
    )
    if encrypted_contests is None:
        return None

    # Create the return object
    encrypted_ballot = make_ciphertext_ballot(
        ballot.object_id,
        ballot.style_id,
        internal_manifest.manifest_hash,
        encryption_seed,
        encrypted_contests,
        random_master_nonce,
    )

    if not encrypted_ballot.code:
        return None

    if not should_verify_proofs:
        return encrypted_ballot

    # Verify the proofs
    if encrypted_ballot.is_valid_encryption(
        internal_manifest.manifest_hash,
        context.elgamal_public_key,
        context.crypto_extended_base_hash,
    ):
        return encrypted_ballot
    return None  # log will have happened earlier


def encrypt_ballot_contests(
    ballot: PlaintextBallot,
    description: InternalManifest,
    context: CiphertextElectionContext,
    nonce_seed: ElementModQ,
    should_verify_proofs: bool = False,
) -> Optional[List[CiphertextBallotContest]]:
    """Encrypt contests from a plaintext ballot with a specific style"""
    encrypted_contests: List[CiphertextBallotContest] = []

    # Only iterate on contests for this specific ballot style
    for ballot_style_contest in description.get_contests_for(ballot.style_id):
        use_contest = None
        for contest in ballot.contests:
            if contest.object_id == ballot_style_contest.object_id:
                use_contest = contest
                break

        # no selections provided for the contest, so create a placeholder contest
        if not use_contest:
            use_contest = contest_from(ballot_style_contest)

        encrypted_contest = encrypt_contest(
            use_contest,
            ballot_style_contest,
            context.elgamal_public_key,
            context.crypto_extended_base_hash,
            nonce_seed,
            should_verify_proofs=should_verify_proofs,
        )

        if encrypted_contest is None:
            return None
        encrypted_contests.append(get_optional(encrypted_contest))
    return encrypted_contests
