from dataclasses import dataclass, field
from multiprocessing import Pool, cpu_count
from typing import Dict, Optional, List, Set

from .decryption_share import (
    CiphertextDecryptionSelection,
    CiphertextPartialDecryptionSelection,
    CiphertextDecryptionContest,
    CiphertextPartialDecryptionContest,
    DecryptionShare,
    PartialDecryptionShare,
)
from .election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from .dlog import discrete_log
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext
from .guardian import Guardian
from .tally import CiphertextTally, CiphertextTallySelection
from .group import ElementModP, div_p, mult_p
from .logs import log_warning

AVAILABLE_GUARDIAN_ID = str
MISSING_GUARDIAN_ID = str
OBJECT_ID = str


@dataclass
class PlaintextTallySelection(ElectionObjectBase):
    """
    A plaintext Tally Selection is a decrypted selection of a contest
    """

    plaintext: int
    # g^tally or M in the spec
    value: ElementModP

    message: ElGamalCiphertext


@dataclass
class PlaintextTallyContest(ElectionObjectBase):
    """
    A plaintext Tally Contest is a collection of plaintext selections
    """

    selections: Dict[OBJECT_ID, PlaintextTallySelection]


@dataclass
class PlaintextTally(ElectionObjectBase):
    """
    The plaintext representation of all contests in the election
    """

    contests: Dict[OBJECT_ID, PlaintextTallyContest]


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

    _available_guardians: Dict[AVAILABLE_GUARDIAN_ID, Guardian] = field(
        default_factory=lambda: {}
    )
    _missing_guardians: Set[MISSING_GUARDIAN_ID] = field(default_factory=lambda: set())

    # A collection of Decryption Shares for each Available Guardian
    _decryption_shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare] = field(
        default_factory=lambda: {}
    )

    # A collection of Partial Decryption Shares for each Available Guardian
    _partial_decryption_shares: Dict[
        MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, PartialDecryptionShare]
    ] = field(default_factory=lambda: {})

    def announce(self, guardian: Guardian) -> Optional[DecryptionShare]:
        """
        Announce that a Guardian is present and participating in the decryption.  
        A Decryption Share will be generated for the Guardian

        :param guardian: The guardian who will participate in the decryption.
        :return: a `DecryptionShare` for this `Guardian` or `None` if there is an error.
        """

        # Only allow a guardian to announce once
        if guardian.object_id in self._available_guardians:
            log_warning(f"guardian {guardian.object_id} already announced")
            return None

        # Compute the Decryption Share for the guardian
        share = compute_decryption_share(
            guardian, self._ciphertext_tally, self._encryption
        )
        if share is None:
            return None

        # Submit the share
        if self._submit_decryption_share(share):
            self._available_guardians[guardian.object_id] = guardian
            return share
        else:
            log_warning(
                f"announce could not submit decryption share for {guardian.object_id}"
            )
            return None

    def compensate(
        self, missing_guardian_id: str
    ) -> Optional[List[PartialDecryptionShare]]:
        """
        Compensate for a missing guardian by reconstructing the share using the available guardians.

        :param missing_guardian_id: the guardian that failed to `announce`.
        :return: a collection of `PartialDecryptionShare` generated from all available guardians 
                 or `None if there is an error
        """

        partial_decryptions: List[PartialDecryptionShare] = List()

        # Loop through each of the available guardians
        # and calculate a partial for the missing one
        for guardian in self._available_guardians.values():
            partial = compute_partial_decryption_share(
                guardian, missing_guardian_id, self._ciphertext_tally
            )
            if partial is None:
                log_warning(f"compensation failed for missing: {missing_guardian_id}")
                break
            else:
                partial_decryptions.append(partial)

        # Verify generated the correct number of partials
        if len(partial_decryptions) != len(self._available_guardians):
            log_warning(
                f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}"
            )
            return None
        else:
            return partial_decryptions

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
            return self._decrypt_tally()

        # If missing guardians compensate for the missing guardians
        for missing in self._missing_guardians:
            partial_decryptions = self.compensate(missing)
            if partial_decryptions is None:
                log_warning(f"get plaintext tally failed compensating for {missing}")
                return None
            self._submit_partial_decryption_shares(partial_decryptions)

        return self._decrypt_tally()

    def _decrypt_tally(self) -> Optional[PlaintextTally]:
        """
        Try to decrypt the tally
        """
        cpu_pool = Pool(cpu_count())
        contests: Dict[OBJECT_ID, PlaintextTallyContest] = {}

        # iterate through the tally contests
        for contest in self._ciphertext_tally.cast.values():
            selections: Dict[OBJECT_ID, PlaintextTallySelection] = {}
            plaintext_selections = cpu_pool.starmap(
                self._decrypt_selection,
                [
                    (selection, self._decryption_shares)
                    for (_, selection) in contest.tally_selections.items()
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
        return PlaintextTally(self._ciphertext_tally.object_id, contests)

    def _decrypt_selection(
        self,
        selection: CiphertextTallySelection,
        shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare],
    ) -> Optional[PlaintextTallySelection]:
        """
        Compute the decryption for a specific selection
        """
        # accumulate all of the shares calculated for the selection
        all_shares_product_M = mult_p(
            *[
                selection_.share
                for share in shares.values()
                for contest_ in share.contests.values()
                for selection_ in contest_.selections.values()
                if selection_.object_id == selection.object_id
            ]
        )

        # Calculate 𝑀=𝐵⁄(∏𝑀𝑖) mod 𝑝.
        decrypted_value = div_p(selection.message.beta, all_shares_product_M)
        return PlaintextTallySelection(
            selection.object_id,
            discrete_log(decrypted_value),
            decrypted_value,
            selection.message,
        )

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

    def _submit_partial_decryption_shares(
        self, shares: List[PartialDecryptionShare]
    ) -> bool:
        """
        Submit partial decruyption shares to be used in the decryption
        """
        for share in shares:
            self._submit_partial_decryption_share(share)

        return True

    def _submit_partial_decryption_share(self, share: PartialDecryptionShare) -> bool:
        """
        Submit partial decryption share to be used in the decryption
        """

        if (
            share.missing_guardian_id in self._partial_decryption_shares
            and share.available_guardian_id
            in self._partial_decryption_shares[share.missing_guardian_id]
        ):
            log_warning(
                f"cannot submit partial for guardian {share.available_guardian_id} on behalf of {share.missing_guardian_id} that already compensated"
            )
            return False

        self._partial_decryption_shares[share.missing_guardian_id][
            share.available_guardian_id
        ] = share

        return True


def compute_decryption_share(
    guardian: Guardian,
    tally: CiphertextTally,
    encryption_context: CiphertextElectionContext,
) -> Optional[DecryptionShare]:
    """
    Compute a decryptions share for a guardian

    :param guardian: The guardian who will partially decrypt the tally
    :param tally: The election tally to decrypt
    :encryption_context: The public election encryption context
    :return: a `DecryptionShare` or `None` if there is an error
    """
    cpu_pool = Pool(cpu_count())
    contests: Dict[OBJECT_ID, CiphertextDecryptionContest] = {}

    for contest in tally.cast.values():
        selections: Dict[OBJECT_ID, CiphertextDecryptionSelection] = {}
        selection_decryptions = cpu_pool.starmap(
            _compute_decryption_for_selection,
            [
                (guardian, selection, encryption_context)
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
            contest.object_id, contest.description_hash, selections
        )

    return DecryptionShare(guardian.object_id, contests)


def _compute_decryption_for_selection(
    guardian: Guardian,
    selection: CiphertextTallySelection,
    encryption_context: CiphertextElectionContext,
) -> Optional[CiphertextDecryptionSelection]:
    """
    Compute a partial decryption for a specific selection

    :param guardian: The guardian who will partially decrypt the tally
    :param selection: The specific selection to decrypt
    :encryption_context: The public election encryption context
    :return: a `CiphertextDecryptionSelection` or `None` if there is an error
    """

    (decryption, proof) = guardian.partially_decrypt(
        selection.message, encryption_context.crypto_extended_base_hash
    )

    if proof.is_valid(
        selection.message,
        guardian.share_election_public_key().key,
        decryption,
        encryption_context.crypto_extended_base_hash,
    ):
        return CiphertextDecryptionSelection(
            selection.object_id, selection.description_hash, decryption, proof
        )
    else:
        log_warning(
            f"compute decryption share proof failed for {guardian.object_id} {selection.object_id}"
        )
        return None


def compute_partial_decryption_share(
    available_guardian: Guardian, missing_guardian_id: str, tally: CiphertextTally
) -> Optional[PartialDecryptionShare]:
    """
    Compute a partial decryption share for a missing guardian
    """
    return None
