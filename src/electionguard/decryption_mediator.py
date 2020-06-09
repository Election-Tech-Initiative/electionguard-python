from dataclasses import dataclass, field, InitVar
from secrets import randbelow
from typing import Dict, Optional, List, Set

from .ballot import (
    CiphertextBallot,
    CiphertextBallotContest,
    CiphertextBallotSelection,
    PlaintextBallot,
    PlaintextBallotContest,
    PlaintextBallotSelection,
)
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
    ContestDescriptionWithPlaceholders,
    SelectionDescription,
)
from .chaum_pedersen import ConstantChaumPedersenProof, make_constant_chaum_pedersen
from .dlog import discrete_log
from .nonces import Nonces
from .election_object_base import ElectionObjectBase
from .elgamal import ElGamalCiphertext
from .guardian import Guardian
from .tally import CiphertextTally, CiphertextTallyContest, CiphertextTallySelection
from .group import ElementModP, ElementModQ, Q, int_to_q_unchecked, div_p, mult_p
from .hash import hash_elems
from .logs import log_warning
from .nonces import Nonces
from .utils import get_optional

AVAILABLE_GUARDIAN_ID = str
MISSING_GUARDIAN_ID = str


@dataclass
class PlaintextTallySelection(ElectionObjectBase):
    """
    A plaintext tallied selection
    """

    plaintext: int
    # g^tally or M in the spec
    value: ElementModP

    message: ElGamalCiphertext


@dataclass
class PlaintextTallyContest(ElectionObjectBase):
    """
    A plaintext tallied contest
    """

    selections: Dict[str, PlaintextTallySelection]


@dataclass
class PlaintextTally(ElectionObjectBase):
    """
    The plaintext representation of the election
    """

    contests: Dict[str, PlaintextTallyContest]


@dataclass
class DecryptionMediator:
    """
    Decryption Mediator
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
        MISSING_GUARDIAN_ID, Dict[MISSING_GUARDIAN_ID, PartialDecryptionShare]
    ] = field(default_factory=lambda: {})

    def announce(self, guardian: Guardian) -> Optional[DecryptionShare]:
        """
        Announce that a Guardian is present.  A Decryption Share will be generated for the Guardian
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

    # TODO: should return a Dict?
    def compensate(
        self, missing_guardian_id: str
    ) -> Optional[List[PartialDecryptionShare]]:
        """
        Compensate
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

        # Verify we generated the correct number of partials
        if len(partial_decryptions) != len(self._available_guardians):
            log_warning(
                f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}"
            )
            return None
        else:
            return partial_decryptions

    def get_plaintext_tally(self) -> Optional[PlaintextTally]:
        """
        Get the plaintext tally for the election
        """

        if self._plaintext_tally is not None:
            return self._plaintext_tally

        # Make sure we have a Quorum of Guardians that have announced
        if len(self._available_guardians) < self._encryption.quorum:
            log_warning(
                "cannot get plaintext tally with less than quorum available guardians"
            )
            return None

        # If all Guardians are present we can decrypt the tally
        if len(self._available_guardians) == self._encryption.number_of_guardians:
            return self._decrypt_tally()

        for missing in self._missing_guardians:
            partial_decryptions = self.compensate(missing)
            if partial_decryptions is None:
                log_warning(f"get plaintext tally failed compensating for {missing}")
                return None
            self._submit_partial_decryption_shares(partial_decryptions)

        return self._decrypt_tally()

    def _decrypt_tally(self) -> Optional[PlaintextTally]:
        """
        Decrypt tally
        """
        plaintext_contests: Dict[str, PlaintextTallyContest] = {}
        for contest in self._ciphertext_tally.cast.values():
            plaintext_selections: Dict[str, PlaintextTallySelection] = {}
            for selection in contest.tally_selections.values():
                all_shares_product_M = mult_p(
                    *[
                        selection.share
                        for share in self._decryption_shares.values()
                        for contest in share.contests.values()
                        for selection in contest.selections.values()
                    ]
                )
                # todo: move this somewhere else
                # also, the decrypt known product may work here
                decrypted_value = div_p(selection.message.beta, all_shares_product_M)
                plaintext_selections[selection.object_id] = PlaintextTallySelection(
                    selection.object_id,
                    discrete_log(decrypted_value),
                    decrypted_value,
                    selection.message,
                )
            plaintext_contests[contest.object_id] = PlaintextTallyContest(
                contest.object_id, plaintext_selections
            )
        return PlaintextTally(self._ciphertext_tally.object_id, plaintext_contests)

    def _submit_decryption_share(self, share: DecryptionShare) -> bool:
        """
        Submit the decryption share
        """

        self._decryption_shares[share.guardian_id] = share
        return True

    def _submit_partial_decryption_shares(
        self, shares: List[PartialDecryptionShare]
    ) -> bool:
        """
        Submit partial decrruyption shares
        """
        for share in shares:
            self._submit_partial_decryption_share(share)

        return True

    def _submit_partial_decryption_share(self, share: PartialDecryptionShare) -> bool:
        """
        Submit partial decryption share
        """
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
    Compute a decryptions hare for a guardian
    """
    # TODO: use all cores
    contests: Dict[str, CiphertextDecryptionContest] = {}

    for contest in tally.cast.values():
        selections: Dict[str, CiphertextDecryptionSelection] = {}
        for selection in contest.tally_selections.values():
            (decryption, proof) = guardian.partially_decrypt_tally(
                selection.message, encryption_context.crypto_extended_base_hash
            )
            if proof.is_valid(
                selection.message,
                guardian.share_election_public_key().key,
                decryption,
                encryption_context.crypto_extended_base_hash,
            ):
                selections[selection.object_id] = CiphertextDecryptionSelection(
                    selection.object_id, selection.description_hash, decryption, proof
                )
            else:
                log_warning(
                    f"compute decryption share proof failed for {guardian.object_id} {selection.object_id}"
                )
                return None
        contests[contest.object_id] = CiphertextDecryptionContest(
            contest.object_id, contest.description_hash, selections
        )

    return DecryptionShare(guardian.object_id, contests)


def compute_partial_decryption_share(
    available_guardian: Guardian, missing_guardian_id: str, tally: CiphertextTally
) -> Optional[PartialDecryptionShare]:
    """
    Compute a partial decryption share for a missing guardian
    """
    return None
