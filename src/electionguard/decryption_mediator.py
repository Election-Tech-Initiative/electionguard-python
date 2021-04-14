from typing import Dict, List, Optional

from .ballot import SubmittedBallot
from .decryption import (
    compute_lagrange_coefficients_for_guardians,
    reconstruct_decryption_share,
    reconstruct_decryption_share_for_ballot,
)
from .decryption_share import DecryptionShare, CompensatedDecryptionShare
from .decrypt_with_shares import decrypt_ballot, decrypt_tally
from .election import CiphertextElectionContext
from .key_ceremony import ElectionPublicKey
from .key_ceremony_mediator import GuardianPair
from .logs import log_info, log_warning
from .tally import (
    CiphertextTally,
    PlaintextTally,
)
from .types import BALLOT_ID, GUARDIAN_ID, MEDIATOR_ID


class DecryptionMediator:
    """
    The Decryption Mediator composes partial decryptions from each Guardian
    to form a decrypted representation of an election tally
    """

    # pylint: disable=too-many-instance-attributes
    id: MEDIATOR_ID
    _context: CiphertextElectionContext

    # Guardians
    _available_guardians: Dict[GUARDIAN_ID, ElectionPublicKey]
    _missing_guardians: Dict[GUARDIAN_ID, ElectionPublicKey]

    # Decryption Shares
    _tally_shares: Dict[GUARDIAN_ID, DecryptionShare]
    _ballot_shares: Dict[BALLOT_ID, Dict[GUARDIAN_ID, DecryptionShare]]

    # Compensated Shares
    _compensated_tally_shares: Dict[GuardianPair, CompensatedDecryptionShare]
    _compensated_ballot_shares: Dict[
        BALLOT_ID, Dict[GuardianPair, CompensatedDecryptionShare]
    ]

    def __init__(self, id: MEDIATOR_ID, context: CiphertextElectionContext):
        self.id = id
        self._context = context

        self._available_guardians = {}
        self._missing_guardians = {}

        self._tally_shares = {}
        self._ballot_shares = {}

        self._compensated_tally_shares = {}
        self._compensated_ballot_shares = {}

    def announce(
        self,
        guardian_key: ElectionPublicKey,
        tally_share: DecryptionShare,
        ballot_shares: Dict[BALLOT_ID, DecryptionShare] = None,
    ) -> None:
        """
        Announce that a Guardian is present and participating in the decryption.
        A guardian announces by presenting their id and their shares of the decryption

        :param guardian_key: The election public key of the guardian who will participate in the decryption.
        :param tally_share: Guardian's decryption share of the tally
        :param ballot_shares: Guardian's decryption shares of the ballots
        """

        guardian_id = guardian_key.owner_id

        # Only allow a guardian to announce once
        if guardian_id in self._available_guardians:
            log_info(f"guardian {guardian_id} already announced")
            return

        self._save_tally_share(guardian_id, tally_share)

        if ballot_shares is not None:
            self._save_ballot_shares(guardian_id, ballot_shares)

        self._mark_available(guardian_key)

    def announce_missing(self, missing_guardian_key: ElectionPublicKey) -> None:
        """
        Announce that a Guardian is missing and not participating in the decryption.

        :param missing_guardian_key: The election public key of the missing guardian
        """
        missing_guardian_id = missing_guardian_key.owner_id

        # If guardian is available, can't be marked missing
        if missing_guardian_id in self._available_guardians:
            log_info(f"guardian {missing_guardian_id} already announced")
            return

        self._mark_missing(missing_guardian_key)

    def validate_missing_guardians(
        self, guardian_keys: List[ElectionPublicKey]
    ) -> bool:
        """
        Check the guardian's collections of keys and ensure the public keys
        match for the guardians
        """

        # Check this guardian's collection of public keys
        # for other guardians that have not announced
        missing_guardians: Dict[GUARDIAN_ID, ElectionPublicKey] = {
            guardian_key.owner_id: guardian_key
            for guardian_key in guardian_keys
            if guardian_key.owner_id not in self._available_guardians
        }

        # Check that the public keys match for any missing guardians already reported
        # note this check naively assumes that the first guardian to annouce is telling the truth
        # but for this implementation it is simply a sanity check on the input data.
        # a consuming application should implement better validation of the guardian state
        # before announcing a guardian is available for decryption.
        for guardian_id, public_key in missing_guardians.items():
            if guardian_id in self._missing_guardians.keys():
                if self._missing_guardians[guardian_id] != public_key:
                    log_warning(
                        (
                            f"announce guardian: {guardian_id} "
                            f"expected public key mismatch for missing {guardian_id}"
                        )
                    )
                    return False
            else:
                self._missing_guardians[guardian_id] = missing_guardians[guardian_id]
        return True

    def announcement_complete(self) -> bool:
        """
        Determine if the announcement phase is complete
        :return: True if announcement complete
        """
        # If a quorum not announced, not ready
        if len(self._available_guardians) < self._context.quorum:
            log_warning("cannot decrypt with less than quorum available guardians")
            return False

        # If guardians missing or available not accounted for, not ready
        if (
            len(self._available_guardians) + len(self._missing_guardians)
            != self._context.number_of_guardians
        ):
            log_warning(
                "cannot decrypt without accounting for all guardians missing or present"
            )
            return False
        return True

    def get_available_guardians(self) -> List[ElectionPublicKey]:
        """
        Get all available guardian keys
        :return: All available guardians election public keys
        """
        return list(self._available_guardians.values())

    def get_missing_guardians(self) -> List[ElectionPublicKey]:
        """
        Get all missing guardian keys
        :return: All missing guardians election public keys
        """
        return list(self._missing_guardians.values())

    def receive_tally_compensation_share(
        self, tally_compensation_share: CompensatedDecryptionShare
    ) -> None:
        self._compensated_tally_shares[
            GuardianPair(
                tally_compensation_share.guardian_id,
                tally_compensation_share.missing_guardian_id,
            )
        ] = tally_compensation_share

    def receive_ballot_compensation_shares(
        self, ballot_compensation_shares: Dict[BALLOT_ID, CompensatedDecryptionShare]
    ) -> None:
        for ballot_id, share in ballot_compensation_shares.items():
            ballot_shares = self._compensated_ballot_shares.get(ballot_id)
            if not ballot_shares:
                ballot_shares = {}
            ballot_shares[
                GuardianPair(share.guardian_id, share.missing_guardian_id)
            ] = share
            self._compensated_ballot_shares[ballot_id] = ballot_shares

    def reconstruct_shares_for_tally(self, ciphertext_tally: CiphertextTally) -> None:
        lagrange_coefficients = compute_lagrange_coefficients_for_guardians(
            list(self._available_guardians.values())
        )
        for (
            missing_guardian_id,
            missing_guardian_key,
        ) in self._missing_guardians.items():
            # Share already reconstructed
            if missing_guardian_id in self._tally_shares:
                continue

            compensated_shares = _filter_by_missing_guardian(
                missing_guardian_id, self._compensated_tally_shares
            )

            reconstructed_share = reconstruct_decryption_share(
                missing_guardian_key,
                ciphertext_tally,
                compensated_shares,
                lagrange_coefficients,
            )

            if reconstruct_decryption_share is None:
                log_warning(
                    f"failed to reconstruct tally share for missing guardian {missing_guardian_id}"
                )

            # Add reconstructed share into tally shares
            self._tally_shares[missing_guardian_id] = reconstructed_share

    def reconstruct_shares_for_ballots(
        self, ciphertext_ballots: List[SubmittedBallot]
    ) -> None:
        lagrange_coefficients = compute_lagrange_coefficients_for_guardians(
            list(self._available_guardians.values())
        )
        for ciphertext_ballot in ciphertext_ballots:
            ballot_id = ciphertext_ballot.object_id
            ballot_shares = self._ballot_shares[ballot_id]

            for (
                missing_guardian_id,
                missing_guardian_key,
            ) in self._missing_guardians.items():
                # Share already reconstructed
                if missing_guardian_id in ballot_shares:
                    continue

                compensated_shares = _filter_by_missing_guardian(
                    missing_guardian_id, self._compensated_ballot_shares[ballot_id]
                )

                reconstructed_share = reconstruct_decryption_share_for_ballot(
                    missing_guardian_key,
                    ciphertext_ballot,
                    compensated_shares,
                    lagrange_coefficients,
                )

                if reconstructed_share is None:
                    log_warning(
                        f"failed to reconstruct ballot share for {ballot_id} for missing guardian {missing_guardian_id}"
                    )

                ballot_shares[missing_guardian_id] = reconstructed_share

            # Add shares into ballot shares
            self._ballot_shares[ballot_id] = ballot_shares

    def get_plaintext_tally(
        self, ciphertext_tally: CiphertextTally
    ) -> Optional[PlaintextTally]:
        """
        Get the plaintext tally for the election by composing each Guardian's
        decrypted representation of each selection into a decrypted representation

        :return: a `PlaintextTally` or `None`
        """

        if not self.announcement_complete() or not self._ready_to_decrypt(
            self._tally_shares
        ):
            return None

        return decrypt_tally(
            ciphertext_tally,
            self._tally_shares,
            self._context.crypto_extended_base_hash,
        )

    def get_plaintext_ballots(
        self, ciphertext_ballots: List[SubmittedBallot]
    ) -> Optional[Dict[BALLOT_ID, PlaintextTally]]:
        """
        Get the plaintext ballots for the election by composing each Guardian's
        decrypted representation of each selection into a decrypted representation
        This is typically used in the spoiled ballot use case.

        :return: a Plaintext Ballots or `None`
        """

        if not self.announcement_complete():
            return None

        ballots = {}

        for ciphertext_ballot in ciphertext_ballots:
            ballot_shares = self._ballot_shares.get(ciphertext_ballot.object_id)
            if not ballot_shares or not self._ready_to_decrypt(ballot_shares):
                # Skip ballot if not ready to decrypt
                continue
            ballot = decrypt_ballot(
                ciphertext_ballot,
                ballot_shares,
                self._context.crypto_extended_base_hash,
            )

            if ballot:
                ballots[ballot.object_id] = ballot

        return ballots

    def _save_tally_share(
        self, guardian_id: GUARDIAN_ID, guardians_tally_share: DecryptionShare
    ) -> None:
        """Save a guardians tally share"""
        self._tally_shares[guardian_id] = guardians_tally_share

    def _save_ballot_shares(
        self,
        guardian_id: GUARDIAN_ID,
        guardians_ballot_shares: Dict[BALLOT_ID, DecryptionShare],
    ) -> None:
        """Save a guardian's set of ballot shares"""
        for ballot_id, guardian_ballot_share in guardians_ballot_shares.items():
            shares = self._ballot_shares.get(ballot_id)
            if shares is None:
                shares = {}
            shares[guardian_id] = guardian_ballot_share
            self._ballot_shares[ballot_id] = shares

    def _mark_available(self, guardian_key: ElectionPublicKey) -> None:
        """
        This guardian removes itself from the
        missing list since it generated a valid share
        """
        guardian_id = guardian_key.owner_id
        self._available_guardians[guardian_id] = guardian_key
        if guardian_id in self._missing_guardians:
            self._missing_guardians.pop(guardian_id)

    def _mark_missing(self, guardian_key: ElectionPublicKey) -> None:
        """"""
        self._missing_guardians[guardian_key.owner_id] = guardian_key

    def _ready_to_decrypt(self, shares: Dict[GUARDIAN_ID, DecryptionShare]) -> bool:
        """Shares are ready to decrypt"""
        # If all guardian shares are represented including if necessary
        # the missing guardians reconstructed shares, the decryption can be made
        return len(shares) == self._context.number_of_guardians


def _filter_by_missing_guardian(
    missing_guardian_id: GUARDIAN_ID,
    shares: Dict[GuardianPair, CompensatedDecryptionShare],
) -> Dict[GUARDIAN_ID, CompensatedDecryptionShare]:
    """
    Filter a guardian pair and compensated share dictionary by missing guardian
    """
    missing_guardian_shares = {}
    for pair, share in shares.items():
        if pair.designated_id is missing_guardian_id:
            missing_guardian_shares[pair.owner_id] = share
    return missing_guardian_shares
