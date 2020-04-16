from typing import Optional, List
from distutils import util

from .chaum_pedersen import make_constant_chaum_pedersen, make_disjunctive_chaum_pedersen
from .elgamal import elgamal_add, elgamal_encrypt
from .group import add_q, Q, ElementModP, ElementModQ, flatmap_optional
from .hash import hash_elems
from .logs import log_warning
from .nonces import Nonces
from .ballot import Ballot, BallotContest, BallotSelection
from .election import Election, ContestDescription, SelectionDescription

from secrets import randbelow

class EncryptionCompositor(object):

    pass

def selection_from(description: SelectionDescription, is_placeholder: bool = False, is_affirmative: bool = False) -> BallotSelection:
    log_warning(f"making selection_from: {description.object_id} {is_placeholder} {is_affirmative}")
    return BallotSelection(description.object_id, is_placeholder, str(is_affirmative))

def placeholder_selection_description_from(description: ContestDescription, sequence_order: int) -> SelectionDescription:
    """
    Generates a placeholder selection description that is unique so it can be hashed
    """
    placeholder = f"{description.object_id}-{sequence_order}"
    return SelectionDescription(placeholder, placeholder, sequence_order)

def contest_from(description: ContestDescription) -> BallotContest:

    selections: List[BallotSelection] = list()

    for selection_description in description.ballot_selections:
        selections.append(selection_from(selection_description))

    return BallotContest(
        description.object_id,
        selections
    )

def plaintext_representation(from_string: str) -> int:
    """
    represent a Truthy string as 1, or if the string is Falsy 0
    """
    # TODO: Support integer votes greater than 1 for cases such as cumulative voting

    as_bool = False
    try:
        as_bool = util.strtobool(from_string.lower())
    except ValueError:
        log_warning(f"plaintext: {from_string.lower()} {as_int}")

    as_int = int(as_bool)
    return as_int

def encrypt_selection(
    selection: BallotSelection, 
    selection_description: SelectionDescription, 
    elgamal_public_key: ElementModP, 
    seed: ElementModQ, is_placeholder: bool = False) -> Optional[BallotSelection]:

    # TODO: Validate Input

    nonce_sequence = Nonces(selection_description.crypto_hash(), seed)
    selection_nonce = nonce_sequence[selection_description.sequence_order]
    selection_representation = plaintext_representation(selection.plaintext)

    encrypted_selection = BallotSelection(selection.object_id, is_placeholder)
    encrypted_selection.message = elgamal_encrypt(
        selection_representation,
        selection_nonce,
        elgamal_public_key
    )

    # Generate the hash
    encrypted_selection.crypto_hash_with(selection_description.crypto_hash())

    # Generate the Proof
    # TODO: move the proof generation blocks into the object itself?
    encrypted_selection.proof = flatmap_optional(
        encrypted_selection.message,
        lambda c: make_disjunctive_chaum_pedersen(
            c,
            selection_nonce,
            elgamal_public_key,
            next(iter(nonce_sequence)),
            selection_representation,
        )
    )

    encrypted_selection.nonce = selection_nonce

    if encrypted_selection.is_valid(selection_description.crypto_hash(), elgamal_public_key):
        return encrypted_selection
    else:
        log_warning(f"mismatching selection proof for selection {encrypted_selection.object_id}")
        return None

def encrypt_contest(
    contest: BallotContest, 
    contest_description: ContestDescription, 
    elgamal_public_key: ElementModP, 
    seed: ElementModQ) -> Optional[BallotContest]:

    # TODO: Validate Input

    # account for sequence id
    nonce_sequence = Nonces(contest_description.crypto_hash(), seed)
    contest_nonce = nonce_sequence[contest_description.sequence_order]

    encrypted_selections: List[BallotSelection] = list()

    selection_count = 0
    highest_sequence_order = 0
    
    for description in contest_description.ballot_selections:
        has_selection = False

        # track the higest sequence order
        if description.sequence_order > highest_sequence_order: 
            highest_sequence_order = description.sequence_order

        # iterate over the actual selections for each contest description
        # and apply the selected value if it exists.  If it does not, an explicit
        # false is entered instead and the selection_count is not incremented
        # this allows consumers to only pass in the relevant selections made by a voter
        for selection in contest.ballot_selections:
            if selection.object_id is description.object_id:
                # track the selection count so we can append the appropriate number
                # of true placeholder votes at the end
                has_selection = True
                selection_count += plaintext_representation(selection.plaintext)
                encrypted_selection = encrypt_selection(
                    selection, 
                    description, 
                    elgamal_public_key, 
                    contest_nonce
                )
        if not has_selection:
        # No selection was made for this possible value
        # so we explicitly set it to false

            encrypted_selection = encrypt_selection(
                selection_from(description), 
                description, 
                elgamal_public_key, 
                contest_nonce
            )
        encrypted_selections.append(encrypted_selection)

    # Handle Placeholder selections
    # TODO: would be better to homomorphically add the encrypted selections together
    # to derive the number of true placeholder votes we need to add
    # instead of tracking the selection_count as a representation of the plaintext values

    # Add a placeholder selection for each possible seat in the contest
    for i in range(contest_description.number_elected):
        log_warning(f"selection count: {selection_count} elected: {contest_description.number_elected}")
        # for undervotes, select the placeholder value as true for each available seat
        # note this pattern is used since DisjuctiveChaumPedersen expects a 0 or 1
        # so each seat can only have a maximum value of 1
        select_placeholder = False
        if selection_count < contest_description.number_elected:
            
            select_placeholder = True
            selection_count += 1

        encrypted_selection = encrypt_selection(
                    selection_from(
                        placeholder_selection_description_from(
                            contest_description, 
                            highest_sequence_order + i),
                            True,
                            select_placeholder), 
                    description, 
                    elgamal_public_key, 
                    contest_nonce
                )
        encrypted_selections.append(encrypted_selection)

    # TODO: support other cases such as cumulative voting
    if selection_count < contest_description.votes_allowed:
        log_warning("mismatching selection count: only n-of-m style elections are currently supported")
        pass

    # Generate the hash
    encrypted_contest = BallotContest(contest.object_id, encrypted_selections)
    encrypted_contest.crypto_hash_with(contest_description.crypto_hash())

    # homomorphic add the encrypted representations together
    elgamal_accumulation = elgamal_add(*[selection.message for selection in encrypted_selections])
    aggregate_nonce = add_q(*[selection.nonce for selection in encrypted_selections])

    # Generate and Verify Proof
    encrypted_contest.proof = make_constant_chaum_pedersen(
        elgamal_accumulation,
        contest_description.number_elected,
        aggregate_nonce,
        elgamal_public_key,
        next(iter(nonce_sequence)),
    )
    encrypted_contest.nonce = contest_nonce

    # Verify the proof
    if encrypted_contest.is_valid(contest_description.crypto_hash(), elgamal_public_key):
        return encrypted_contest
    else:
        log_warning(f"mismatching contest proof for contest {encrypted_contest.object_id}")
        return None

def encrypt_ballot(
    ballot: Ballot, 
    election_metadata: Election, 
    elgamal_public_key: ElementModP, 
    seed: ElementModQ) -> Optional[Ballot]:

    # TODO: Verify Input

    election_hash = election_metadata.crypto_extended_hash(elgamal_public_key)
    random_master_nonce = randbelow(Q)
    hashed_ballot_nonce = hash_elems(election_hash, ballot.object_id, random_master_nonce)

    # Determine the relevant range of contests for this ballot style
    styles = list(filter(lambda i: i.object_id is ballot.ballot_style, election_metadata.ballot_styles))
    gp_unit_ids = [style.geopolitical_unit_id for style in styles]

    encrypted_contests: List[BallotContest] = list()

    # only iterate on contests for this specific ballot style
    for description in filter(lambda i: i.electoral_district_id in gp_unit_ids, election_metadata.contests):
        for contest in ballot.contests:
            # encrypt it as specified
            if contest.object_id is description.object_id:
                encrypted_contest = encrypt_contest(
                    contest, 
                    description, 
                    elgamal_public_key, 
                    hashed_ballot_nonce)
            else:
            # the contest was not voted on this ballot,
            # but we still need to encrypt selections for it
                encrypted_contest = encrypt_contest(
                    contest_from(description),
                    description,
                    elgamal_public_key,
                    hashed_ballot_nonce
                )
            encrypted_contests.append(encrypted_contest)

    encrypted_vallot = Ballot(
            ballot.object_id, ballot.ballot_style, encrypted_contests)

    encrypted_vallot.nonce = random_master_nonce

    # TODO: verify the ballot is now well-formed & valid

    # Generate the Hash
    encrypted_vallot.crypto_hash_with(hashed_ballot_nonce)

    # TODO: Generate Tracking code
    tracking_code = "abc123"
    
    if any(encrypted_contests): 
        return 
    else: 
        return None