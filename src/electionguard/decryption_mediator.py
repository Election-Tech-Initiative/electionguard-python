from dataclasses import dataclass, field
from multiprocessing import cpu_count
from multiprocessing.dummy import Pool
from random import sample
from typing import Dict, Optional, List, Set, Union

from .ballot import CiphertextAcceptedBallot, CiphertextBallotSelection
from .decryption_share import (
    BallotDecryptionShare,
    CompensatedBallotDecryptionShare,
    CiphertextDecryptionSelection,
    CiphertextCompensatedDecryptionSelection,
    CiphertextDecryptionContest,
    CiphertextCompensatedDecryptionContest,
    DecryptionShare,
    CompensatedDecryptionShare,
    get_spoiled_shares_for_selection,
)
from .decrypt import (
    decrypt_selection_with_decryption_shares,
    decrypt_tally_contests_with_decryption_shares,
    decrypt_tally_contests_with_decryption_shares_async,
)
from .dlog import discrete_log
from .election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from .election_polynomial import compute_lagrange_coefficient
from .group import ElementModP, ElementModQ, mult_p, pow_p, int_to_p_unchecked, g_pow_p
from .guardian import Guardian
from .key_ceremony import GuardianDataStore, ElectionPublicKey
from .tally import (
    CiphertextTally,
    PlaintextTally,
    CiphertextTallyContest,
    PlaintextTallyContest,
    CiphertextTallySelection,
    PlaintextTallySelection,
)
from .logs import log_debug, log_info, log_warning
from .types import BALLOT_ID, CONTEST_ID, GUARDIAN_ID, SELECTION_ID

AVAILABLE_GUARDIAN_ID = GUARDIAN_ID
MISSING_GUARDIAN_ID = GUARDIAN_ID

GUARDIAN_PUBLIC_KEY = ElementModP


@dataclass
class DecryptionMediator:
    """
    The Decryption Mediator composes partial decryptions from each Guardian 
    to form a decrypted representation of an election tally
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    _ciphertext_tally: CiphertextTally
    _plaintext_tally: Optional[PlaintextTally] = field(default=None)

    # Since spoiled ballots are decrypted, they are just a special case of a tally
    _plaintext_spoiled_ballots: Dict[BALLOT_ID, Optional[PlaintextTally]] = field(
        default_factory=lambda: {}
    )

    # TODO: as GuardianDataStore
    _available_guardians: Dict[AVAILABLE_GUARDIAN_ID, Guardian] = field(
        default_factory=lambda: {}
    )
    _missing_guardians: GuardianDataStore[
        MISSING_GUARDIAN_ID, ElectionPublicKey
    ] = field(default_factory=lambda: GuardianDataStore())

    # TODO: as GuardianDataStore
    _decryption_shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare] = field(
        default_factory=lambda: {}
    )
    """
    A collection of Decryption Shares for each Available Guardian
    """

    _lagrange_coefficients: Dict[
        MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]
    ] = field(default_factory=lambda: {})
    """
    A collection of lagrange coefficients `w_{i,j}` computed by available guardians for each missing guardian
    """

    _compensated_decryption_shares: Dict[
        MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]
    ] = field(default_factory=lambda: {})
    """
    A collection of Compensated Decryption Shares for each Available Guardian
    """

    def announce(self, guardian: Guardian) -> Optional[DecryptionShare]:
        """
        Announce that a Guardian is present and participating in the decryption.  
        A Decryption Share will be generated for the Guardian

        :param guardian: The guardian who will participate in the decryption.
        :return: a `DecryptionShare` for this `Guardian` or `None` if there is an error.
        """

        # Only allow a guardian to announce once
        if guardian.object_id in self._available_guardians:
            log_info(f"guardian {guardian.object_id} already announced")
            return self._decryption_shares[guardian.object_id]

        # Compute the Decryption Share for the guardian
        share = compute_decryption_share(
            guardian, self._ciphertext_tally, self._encryption
        )
        if share is None:
            log_warning(
                f"announce could not generate decryption share for {guardian.object_id}"
            )
            return None

        # Submit the share
        if self._submit_decryption_share(share):
            self._available_guardians[guardian.object_id] = guardian
        else:
            log_warning(
                f"announce could not submit decryption share for {guardian.object_id}"
            )
            return None

        # This guardian removes itself from the
        # missing list since it generated a valid share
        if guardian.object_id in self._missing_guardians.keys():
            self._missing_guardians.pop(guardian.object_id)

        # Check this guardian's collection of public keys
        # for other guardians that have not announced
        missing_guardians: Dict[MISSING_GUARDIAN_ID, ElectionPublicKey] = {
            guardian_id: public_key
            for guardian_id, public_key in guardian.guardian_election_public_keys()
            if guardian_id not in self._available_guardians
        }

        # Check that the public keys match for any missing guardians already reported
        # note this check naively assumes that the first guardian to annouce is telling the truth
        # but for this implementation it is simply a sanity check on the input data.
        # a consuming application should implement better validation of the guardian state
        # before announcing a guardian is available for decryption.
        for guardian_id, public_key in missing_guardians.items():
            if guardian_id in self._missing_guardians.keys():
                if self._missing_guardians.get(guardian_id) != public_key:
                    log_warning(
                        f"announce guardian: {guardian.object_id} expected public key mismatch for missing {guardian_id}"
                    )
                    return None
            else:
                self._missing_guardians.set(guardian_id, missing_guardians[guardian_id])

        return share

    def compensate(
        self, missing_guardian_id: str
    ) -> Optional[List[CompensatedDecryptionShare]]:
        """
        Compensate for a missing guardian by reconstructing the share using the available guardians.

        :param missing_guardian_id: the guardian that failed to `announce`.
        :return: a collection of `CompensatedDecryptionShare` generated from all available guardians
                 or `None if there is an error
        """

        # Only allow a guardian to be compensated for once
        if missing_guardian_id in self._compensated_decryption_shares:
            log_warning(f"guardian {missing_guardian_id} already compensated")
            return list(
                self._compensated_decryption_shares[missing_guardian_id].values()
            )

        compensated_decryptions: List[CompensatedDecryptionShare] = []
        lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ] = {}

        available_sequences = [
            guardian.sequence_order for guardian in self._available_guardians.values()
        ]

        # Loop through each of the available guardians
        # and calculate a partial for the missing one
        for available_guardian in self._available_guardians.values():

            # Compute lagrange coefficients for each of the available guardians
            lagrange_coefficients[
                available_guardian.object_id
            ] = compute_lagrange_coefficient(
                available_guardian.sequence_order,
                *[
                    guardian.sequence_order
                    for guardian in self._available_guardians.values()
                    if guardian.object_id != available_guardian.object_id
                ],
            )

            # Compute the decryption shares
            share = compute_compensated_decryption_share(
                available_guardian,
                missing_guardian_id,
                self._ciphertext_tally,
                self._encryption,
            )
            if share is None:
                log_warning(f"compensation failed for missing: {missing_guardian_id}")
                break
            else:
                compensated_decryptions.append(share)

        # Verify generated the correct number of partials
        if len(compensated_decryptions) != len(self._available_guardians):
            log_warning(
                f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}"
            )
            return None
        else:
            self._lagrange_coefficients[missing_guardian_id] = lagrange_coefficients
            self._submit_compensated_decryption_shares(compensated_decryptions)
            return compensated_decryptions

    def get_plaintext_tally(self, recompute: bool = False) -> Optional[PlaintextTally]:
        """
        Get the plaintext tally for the election by composing each Guardian's 
        decrypted representation of each selection into a decrypted representation

        :param recompute: Specify if the function should recompute the result, even if one already exists.
        :return: a `PlaintextTally` or `None`
        """

        if self._plaintext_tally is not None and not recompute:
            return self._plaintext_tally

        # Make sure a Quorum of Guardians have announced
        if len(self._available_guardians) < self._encryption.quorum:
            log_warning(
                "cannot get plaintext tally with less than quorum available guardians"
            )
            return None

        # If all Guardians are present decrypt the tally
        if len(self._available_guardians) == self._encryption.number_of_guardians:
            return self._decrypt_tally(
                self._ciphertext_tally, self._decryption_shares, self._encryption
            )

        # If missing guardians compensate for the missing guardians
        for missing in self._missing_guardians.keys():
            compensated_decryptions = self.compensate(missing)
            if compensated_decryptions is None:
                log_warning(f"get plaintext tally failed compensating for {missing}")
                return None

        # Reconstruct the missing partial decryptions from the compensation shares
        missing_decryption_shares = self._reconstruct_missing_tally_decryption_shares(
            self._ciphertext_tally,
            self._missing_guardians,
            self._compensated_decryption_shares,
            self._lagrange_coefficients,
        )
        if (
            missing_decryption_shares is None
            or len(missing_decryption_shares) != self._missing_guardians.length()
        ):
            log_warning(f"get plaintext tally failed with missing decryption shares")
            return None

        # merged_decryption_shares: Dict[str, DecryptionShare] = {
        #     **self._decryption_shares,
        #     **missing_decryption_shares,
        # }

        merged_decryption_shares: Dict[str, DecryptionShare] = {}

        for available, share in self._decryption_shares.items():
            merged_decryption_shares[available] = share

        for missing, share in missing_decryption_shares.items():
            merged_decryption_shares[missing] = share

        if len(merged_decryption_shares) != self._encryption.number_of_guardians:
            log_warning(f"get plaintext tally failed with share length mismatch")
            return None

        return self._decrypt_tally(
            self._ciphertext_tally, merged_decryption_shares, self._encryption
        )

    def _decrypt_tally(
        self,
        tally: CiphertextTally,
        shares: Dict[GUARDIAN_ID, DecryptionShare],
        context: CiphertextElectionContext,
    ) -> Optional[PlaintextTally]:
        """
        Try to decrypt the tally
        """
        contests = decrypt_tally_contests_with_decryption_shares(
            tally.cast, shares, context.crypto_extended_base_hash
        )

        if contests is None:
            return None

        spoiled_ballots = self._decrypt_spoiled_ballots(
            tally.spoiled_ballots, shares, context.crypto_extended_base_hash
        )

        if spoiled_ballots is None:
            return None

        return PlaintextTally(tally.object_id, contests, spoiled_ballots)

    def _decrypt_spoiled_ballots_async(
        self,
        spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
        shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare],
        extended_base_hash: ElementModQ,
    ) -> Optional[Dict[BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]]]:
        """
        Decrypt each of the spoiled ballots
        """

        plaintext_spoiled_ballots: Dict[
            BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]
        ] = {}

        cpu_pool = Pool(cpu_count())

        for spoiled_ballot in spoiled_ballots.values():
            contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}
            for contest in spoiled_ballot.contests:
                selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}
                plaintext_selections = cpu_pool.starmap(
                    decrypt_selection_with_decryption_shares,
                    [
                        (
                            selection,
                            get_spoiled_shares_for_selection(
                                spoiled_ballot.object_id, selection.object_id, shares
                            ),
                            extended_base_hash,
                        )
                        for selection in contest.ballot_selections
                    ],
                )

                # verify the plaintext values are received and add them to the collection
                for plaintext in plaintext_selections:
                    if plaintext is None:
                        log_warning(
                            f"could not decrypt tally for contest {contest.object_id}"
                        )
                        return None
                    selections[plaintext.object_id] = plaintext

                contests[contest.object_id] = PlaintextTallyContest(
                    contest.object_id, selections
                )
            plaintext_spoiled_ballots[spoiled_ballot.object_id] = contests

        cpu_pool.close()
        return plaintext_spoiled_ballots

    def _decrypt_spoiled_ballots(
        self,
        spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
        shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare],
        extended_base_hash: ElementModQ,
    ) -> Optional[Dict[BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]]]:
        """
        Decrypt each of the spoiled ballots
        """

        plaintext_spoiled_ballots: Dict[
            BALLOT_ID, Dict[CONTEST_ID, PlaintextTallyContest]
        ] = {}

        for spoiled_ballot in spoiled_ballots.values():
            contests: Dict[CONTEST_ID, PlaintextTallyContest] = {}
            for contest in spoiled_ballot.contests:
                selections: Dict[SELECTION_ID, PlaintextTallySelection] = {}
                for selection in contest.ballot_selections:
                    spoiled_shares = get_spoiled_shares_for_selection(
                        spoiled_ballot.object_id, selection.object_id, shares
                    )
                    plaintext_selection = decrypt_selection_with_decryption_shares(
                        selection, spoiled_shares, extended_base_hash
                    )

                    # verify the plaintext values are received and add them to the collection
                    if plaintext_selection is None:
                        log_warning(
                            f"could not decrypt spoiled ballot {spoiled_ballot.object_id} for contest {contest.object_id} selection {selection.object_id}"
                        )
                        return None
                    selections[plaintext_selection.object_id] = plaintext_selection

                contests[contest.object_id] = PlaintextTallyContest(
                    contest.object_id, selections
                )
            plaintext_spoiled_ballots[spoiled_ballot.object_id] = contests

        return plaintext_spoiled_ballots

    def _reconstruct_missing_tally_decryption_shares(
        self,
        ciphertext_tally: CiphertextTally,
        missing_guardians: GuardianDataStore[MISSING_GUARDIAN_ID, ElectionPublicKey],
        compensated_shares: Dict[
            MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]
        ],
        lagrange_coefficients: Dict[
            MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]
        ],
    ) -> Optional[Dict[MISSING_GUARDIAN_ID, DecryptionShare]]:
        """
        Use all available guardians to reconstruct the missing shares
        """

        reconstructed_shares: Dict[MISSING_GUARDIAN_ID, DecryptionShare] = {}
        for missing_guardian_id, shares in compensated_shares.items():

            # Make sure there is a public key
            public_key = missing_guardians.get(missing_guardian_id)
            if public_key is None:
                log_warning(
                    f"Could not reconstruct tally for {missing_guardian_id} with no public key"
                )
                return None

            # make sure there are computed lagrange coefficients:
            lagrange_coefficients_for_missing: Dict[
                AVAILABLE_GUARDIAN_ID, ElementModQ
            ] = lagrange_coefficients.get(missing_guardian_id, {})
            if not any(lagrange_coefficients):
                log_warning(
                    f"Could not reconstruct tally for {missing_guardian_id} with no lagrange coefficients"
                )
                return None

            # iterate through the tallies and accumulate
            # all of the shares for this guardian
            contests = reconstruct_decryption_contests(
                missing_guardian_id,
                ciphertext_tally.cast,
                shares,
                lagrange_coefficients_for_missing,
            )

            # iterate through the spoiled ballots and accumulate
            # all of the shares for this guardian
            spoiled_ballots = reconstruct_decryption_ballots(
                missing_guardian_id,
                public_key,
                ciphertext_tally.spoiled_ballots,
                shares,
                lagrange_coefficients_for_missing,
            )

            reconstructed_shares[missing_guardian_id] = DecryptionShare(
                missing_guardian_id, public_key.key, contests, spoiled_ballots
            )

        return reconstructed_shares

    def _submit_decryption_share(self, share: DecryptionShare) -> bool:
        """
        Submit the decryption share to be used in the decryption
        """

        if share.guardian_id in self._decryption_shares:
            log_warning(
                f"cannot submit for guardian {share.guardian_id} that already decrypted"
            )
            return False

        self._decryption_shares[share.guardian_id] = share
        return True

    def _submit_compensated_decryption_shares(
        self, shares: List[CompensatedDecryptionShare]
    ) -> bool:
        """
        Submit compensated decryption shares to be used in the decryption
        """

        results = [self._submit_compensated_decryption_share(share) for share in shares]

        return all(results)

    def _submit_compensated_decryption_share(
        self, share: CompensatedDecryptionShare
    ) -> bool:
        """
        Submit compensated decryption share to be used in the decryption
        """

        if (
            share.missing_guardian_id in self._compensated_decryption_shares
            and share.guardian_id
            in self._compensated_decryption_shares[share.missing_guardian_id]
        ):
            log_warning(
                f"cannot submit compensated share for guardian {share.guardian_id} on behalf of {share.missing_guardian_id} that already compensated"
            )
            return False

        if share.missing_guardian_id not in self._compensated_decryption_shares:
            self._compensated_decryption_shares[share.missing_guardian_id] = {}

        self._compensated_decryption_shares[share.missing_guardian_id][
            share.guardian_id
        ] = share

        return True


def compute_decryption_share(
    guardian: Guardian, tally: CiphertextTally, context: CiphertextElectionContext,
) -> Optional[DecryptionShare]:
    """
    Compute a decryptions share for a guardian

    :param guardian: The guardian who will partially decrypt the tally
    :param tally: The election tally to decrypt
    :context: The public election encryption context
    :return: a `DecryptionShare` or `None` if there is an error
    """

    contests = _compute_decryption_for_cast_contests(guardian, tally, context)
    if contests is None:
        return None

    spoiled_ballots = _compute_decryption_for_spoiled_ballots(guardian, tally, context)

    if spoiled_ballots is None:
        return None

    return DecryptionShare(
        guardian.object_id,
        guardian.share_election_public_key().key,
        contests,
        spoiled_ballots,
    )


def compute_compensated_decryption_share(
    guardian: Guardian,
    missing_guardian_id: str,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
) -> Optional[CompensatedDecryptionShare]:
    """
    Compute a compensated decryptions share for a guardian

    :param guardian: The guardian who will partially decrypt the tally
    :param missing_guardian_id: the missing guardian id to compensate
    :param tally: The election tally to decrypt
    :context: The public election encryption context
    :return: a `DecryptionShare` or `None` if there is an error
    """

    contests = _compute_compensated_decryption_for_cast_contests(
        guardian, missing_guardian_id, tally, context
    )
    if contests is None:
        return None

    spoiled_ballots = _compute_compensated_decryption_for_spoiled_ballots(
        guardian, missing_guardian_id, tally, context
    )

    if spoiled_ballots is None:
        return None

    return CompensatedDecryptionShare(
        guardian.object_id,
        missing_guardian_id,
        guardian.share_election_public_key().key,
        contests,
        spoiled_ballots,
    )


# TODO: rename compute decryption share
def _compute_decryption_for_cast_contests(
    guardian: Guardian, tally: CiphertextTally, context: CiphertextElectionContext,
) -> Optional[Dict[CONTEST_ID, CiphertextDecryptionContest]]:
    """
    Compute the decryption for all of the cast contests in the Ciphertext Tally
    """
    cpu_pool = Pool(cpu_count())
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}

    for contest in tally.cast.values():
        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        selection_decryptions = cpu_pool.starmap(
            _compute_decryption_for_selection,
            [
                (guardian, selection, context)
                for (_, selection) in contest.tally_selections.items()
            ],
        )

        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute share for guardian {guardian.object_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextDecryptionContest(
            contest.object_id, guardian.object_id, contest.description_hash, selections
        )
    cpu_pool.close()
    return contests


def _compute_compensated_decryption_for_cast_contests(
    guardian: Guardian,
    missing_guardian_id: str,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
) -> Optional[Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest]]:
    """
    Compute the compensated decryption for all of the cast contests in the Ciphertext Tally
    """
    cpu_pool = Pool(cpu_count())
    contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}

    for contest in tally.cast.values():
        selections: Dict[SELECTION_ID, CiphertextCompensatedDecryptionSelection] = {}
        selection_decryptions = cpu_pool.starmap(
            _compute_compensated_decryption_for_selection,
            [
                (guardian, missing_guardian_id, selection, context)
                for (_, selection) in contest.tally_selections.items()
            ],
        )

        # verify the decryptions are received and add them to the collection
        for decryption in selection_decryptions:
            if decryption is None:
                log_warning(
                    f"could not compute share for guardian {guardian.object_id} contest {contest.object_id}"
                )
                return None
            selections[decryption.object_id] = decryption

        contests[contest.object_id] = CiphertextCompensatedDecryptionContest(
            contest.object_id,
            guardian.object_id,
            missing_guardian_id,
            contest.description_hash,
            selections,
        )
    cpu_pool.close()
    return contests


def _compute_decryption_for_spoiled_ballots(
    guardian: Guardian, tally: CiphertextTally, context: CiphertextElectionContext,
) -> Optional[Dict[BALLOT_ID, BallotDecryptionShare]]:
    """
    Compute the decryption for all spoiled ballots in the Ciphertext Tally
    """
    cpu_pool = Pool(cpu_count())
    spoiled_ballots: Dict[BALLOT_ID, BallotDecryptionShare] = {}

    for spoiled_ballot in tally.spoiled_ballots.values():
        contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
        for contest in spoiled_ballot.contests:
            selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
            selection_decryptions = cpu_pool.starmap(
                _compute_decryption_for_selection,
                [
                    (guardian, selection, context)
                    for selection in contest.ballot_selections
                ],
            )
            # verify the decryptions are received and add them to the collection
            for decryption in selection_decryptions:
                if decryption is None:
                    log_warning(
                        f"could not compute spoiled ballot share for guardian {guardian.object_id} contest {contest.object_id}"
                    )
                    return None
                selections[decryption.object_id] = decryption

            contests[contest.object_id] = CiphertextDecryptionContest(
                contest.object_id,
                guardian.object_id,
                contest.description_hash,
                selections,
            )

        spoiled_ballots[spoiled_ballot.object_id] = BallotDecryptionShare(
            guardian.object_id,
            guardian.share_election_public_key().key,
            spoiled_ballot.object_id,
            contests,
        )
    cpu_pool.close()
    return spoiled_ballots


def _compute_compensated_decryption_for_spoiled_ballots(
    guardian: Guardian,
    missing_guardian_id: MISSING_GUARDIAN_ID,
    tally: CiphertextTally,
    context: CiphertextElectionContext,
) -> Optional[Dict[BALLOT_ID, CompensatedBallotDecryptionShare]]:
    """
    Compute the decryption for all spoiled ballots in the Ciphertext Tally
    """
    cpu_pool = Pool(cpu_count())
    spoiled_ballots: Dict[BALLOT_ID, CompensatedBallotDecryptionShare] = {}

    for spoiled_ballot in tally.spoiled_ballots.values():
        contests: Dict[CONTEST_ID, CiphertextCompensatedDecryptionContest] = {}
        for contest in spoiled_ballot.contests:
            selections: Dict[
                SELECTION_ID, CiphertextCompensatedDecryptionSelection
            ] = {}
            selection_decryptions = cpu_pool.starmap(
                _compute_compensated_decryption_for_selection,
                [
                    (guardian, missing_guardian_id, selection, context)
                    for selection in contest.ballot_selections
                ],
            )
            # verify the decryptions are received and add them to the collection
            for decryption in selection_decryptions:
                if decryption is None:
                    log_warning(
                        f"could not compute compensated spoiled ballot share for guardian {guardian.object_id} missing: {missing_guardian_id} contest {contest.object_id}"
                    )
                    return None
                selections[decryption.object_id] = decryption

            contests[contest.object_id] = CiphertextCompensatedDecryptionContest(
                contest.object_id,
                guardian.object_id,
                missing_guardian_id,
                contest.description_hash,
                selections,
            )

        spoiled_ballots[spoiled_ballot.object_id] = CompensatedBallotDecryptionShare(
            guardian.object_id,
            missing_guardian_id,
            guardian.share_election_public_key().key,
            spoiled_ballot.object_id,
            contests,
        )
    cpu_pool.close()
    return spoiled_ballots


def _compute_decryption_for_selection(
    guardian: Guardian,
    selection: CiphertextTallySelection,
    context: CiphertextElectionContext,
) -> Optional[CiphertextDecryptionSelection]:
    """
    Compute a partial decryption for a specific selection

    :param guardian: The guardian who will partially decrypt the selection
    :param selection: The specific selection to decrypt
    :context: The public election encryption context
    :return: a `CiphertextDecryptionSelection` or `None` if there is an error
    """

    (decryption, proof) = guardian.partially_decrypt(
        selection.message, context.crypto_extended_base_hash
    )

    if proof.is_valid(
        selection.message,
        guardian.share_election_public_key().key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        return CiphertextDecryptionSelection(
            selection.object_id,
            guardian.object_id,
            selection.description_hash,
            decryption,
            proof,
        )
    else:
        log_warning(
            f"compute decryption share proof failed for {guardian.object_id} {selection.object_id} with invalid proof"
        )
        return None


CiphertextSelection = Union[CiphertextBallotSelection, CiphertextTallySelection]


def _compute_compensated_decryption_for_selection(
    available_guardian: Guardian,
    missing_guardian_id: str,
    selection: CiphertextSelection,
    context: CiphertextElectionContext,
) -> Optional[CiphertextCompensatedDecryptionSelection]:
    """
    Compute a compensated decryption share for a specific selection using the 
    avialable guardian's share of the missing guardian's private key polynomial

    :param available_guardian: The available guardian that will partially decrypt the selection
    :param missing_guardian_id: The id of the guardian that is missing
    :param selection: The specific selection to decrypt
    :context: The public election encryption context
    :return: a `CiphertextCompensatedDecryptionSelection` or `None` if there is an error
    """

    compensated = available_guardian.compensate_decrypt(
        missing_guardian_id, selection.message, context.crypto_extended_base_hash
    )

    if compensated is None:
        log_warning(
            f"compute compensated decryption share failed for {available_guardian.object_id} missing: {missing_guardian_id} {selection.object_id}"
        )
        return None

    (decryption, proof) = compensated

    recovery_public_key = available_guardian.recovery_public_key_for(
        missing_guardian_id
    )

    if recovery_public_key is None:
        log_warning(
            f"compute compensated decryption share failed for {available_guardian.object_id} missing recovery key: {missing_guardian_id} {selection.object_id}"
        )
        return None

    if proof.is_valid(
        selection.message,
        recovery_public_key,
        decryption,
        context.crypto_extended_base_hash,
    ):
        share = CiphertextCompensatedDecryptionSelection(
            selection.object_id,
            available_guardian.object_id,
            missing_guardian_id,
            selection.description_hash,
            decryption,
            recovery_public_key,
            proof,
        )
        return share
    else:
        log_warning(
            f"compute compensated decryption share proof failed for {available_guardian.object_id} missing: {missing_guardian_id} {selection.object_id}"
        )
        return None


def reconstruct_decryption_contests(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    cast_tally: Dict[CONTEST_ID, CiphertextTallyContest],
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> Dict[CONTEST_ID, CiphertextDecryptionContest]:
    """
    aa
    """
    # iterate through the tallies and accumulate all of the shares for this guardian
    contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
    for contest_id, tally_contest in cast_tally.items():

        selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
        for (selection_id, tally_selection,) in tally_contest.tally_selections.items():

            # collect all of the shares generated for each selection
            compensated_selection_shares: Dict[
                AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
            ] = {
                available_guardian_id: compensated_selection
                for available_guardian_id, compensated_share in shares.items()
                for compensated_contest_id, compensated_contest in compensated_share.contests.items()
                for compensated_selection_id, compensated_selection in compensated_contest.selections.items()
                if compensated_selection_id == selection_id
            }

            share_pow_p = []
            for available_guardian_id, share in compensated_selection_shares.items():
                share_pow_p.append(
                    pow_p(share.share, lagrange_coefficients[available_guardian_id])
                )

            reconstructed_share = mult_p(*share_pow_p)

            selections[selection_id] = CiphertextDecryptionSelection(
                selection_id,
                missing_guardian_id,
                tally_selection.description_hash,
                reconstructed_share,
                compensated_selection_shares,
            )
        contests[contest_id] = CiphertextDecryptionContest(
            contest_id, missing_guardian_id, tally_contest.description_hash, selections,
        )

    return contests


def reconstruct_decryption_ballots(
    missing_guardian_id: MISSING_GUARDIAN_ID,
    public_key: ElectionPublicKey,
    spoiled_ballots: Dict[BALLOT_ID, CiphertextAcceptedBallot],
    shares: Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare],
    lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ],
) -> Dict[BALLOT_ID, BallotDecryptionShare]:
    """
    aa
    """
    spoiled_ballot_shares: Dict[BALLOT_ID, BallotDecryptionShare] = {}
    for ballot_id, spoiled_ballot in spoiled_ballots.items():
        # iterate through the tallies and accumulate all of the shares for this guardian
        contests: Dict[CONTEST_ID, CiphertextDecryptionContest] = {}
        for contest in spoiled_ballot.contests:

            selections: Dict[SELECTION_ID, CiphertextDecryptionSelection] = {}
            for selection in contest.ballot_selections:

                # collect all of the shares generated for each selection
                compensated_selection_shares: Dict[
                    AVAILABLE_GUARDIAN_ID, CiphertextCompensatedDecryptionSelection
                ] = {
                    available_guardian_id: compensated_selection
                    for available_guardian_id, compensated_share in shares.items()
                    for compensated_ballot_id, compensated_ballot in compensated_share.spoiled_ballots.items()
                    for compensated_contest_id, compensated_contest in compensated_ballot.contests.items()
                    for compensated_selection_id, compensated_selection in compensated_contest.selections.items()
                    if compensated_selection_id == selection.object_id
                }

                # compute the reconstructed share
                reconstructed_share = mult_p(
                    *[
                        pow_p(share.share, lagrange_coefficients[available_guardian_id])
                        for available_guardian_id, share in compensated_selection_shares.items()
                    ]
                )
                selections[selection.object_id] = CiphertextDecryptionSelection(
                    selection.object_id,
                    missing_guardian_id,
                    selection.description_hash,
                    reconstructed_share,
                    compensated_selection_shares,
                )
            contests[contest.object_id] = CiphertextDecryptionContest(
                contest.object_id,
                missing_guardian_id,
                contest.description_hash,
                selections,
            )
        spoiled_ballot_shares[spoiled_ballot.object_id] = BallotDecryptionShare(
            missing_guardian_id, public_key.key, spoiled_ballot.object_id, contests,
        )

    return spoiled_ballot_shares

