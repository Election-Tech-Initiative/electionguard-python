from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from electionguard.ballot import SubmittedBallot

from .auxiliary import AuxiliaryDecrypt
from .decryption import (
    compute_compensated_decryption_share_for_ballot,
    compute_decryption_share,
    compute_compensated_decryption_share,
    compute_decryption_share_for_ballots,
    reconstruct_decryption_share,
    reconstruct_decryption_share_for_ballot,
)
from .decryption_share import DecryptionShare, CompensatedDecryptionShare
from .decrypt_with_shares import decrypt_ballots, decrypt_tally
from .election import (
    CiphertextElectionContext,
    InternalElectionDescription,
)
from .election_polynomial import compute_lagrange_coefficient
from .group import ElementModP, ElementModQ
from .guardian import Guardian
from .key_ceremony import ElectionPublicKey
from .rsa import rsa_decrypt
from .tally import (
    CiphertextTally,
    PlaintextTally,
)
from .logs import log_info, log_warning
from .types import BALLOT_ID, GUARDIAN_ID

AVAILABLE_GUARDIAN_ID = GUARDIAN_ID
MISSING_GUARDIAN_ID = GUARDIAN_ID

GUARDIAN_PUBLIC_KEY = ElementModP
SHARE_LOOKUP = Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare]
COMPENSATED_SHARE_LOOKUP = Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]

# pylint: disable=too-many-instance-attributes
@dataclass
class DecryptionMediator:
    """
    The Decryption Mediator composes partial decryptions from each Guardian
    to form a decrypted representation of an election tally
    """

    _metadata: InternalElectionDescription
    _encryption: CiphertextElectionContext

    # Tally to Decrypt
    _ciphertext_tally: CiphertextTally
    _ciphertext_ballots: Dict[BALLOT_ID, SubmittedBallot]

    # Tally
    _tally_shares: Dict[AVAILABLE_GUARDIAN_ID, DecryptionShare] = field(
        default_factory=lambda: {}
    )

    # Ballot
    _ballot_shares: Dict[
        AVAILABLE_GUARDIAN_ID, Dict[BALLOT_ID, DecryptionShare]
    ] = field(default_factory=lambda: {})

    # Guardians
    _available_guardians: Dict[AVAILABLE_GUARDIAN_ID, Guardian] = field(
        default_factory=lambda: {}
    )
    _missing_guardians: Dict[MISSING_GUARDIAN_ID, ElectionPublicKey] = field(
        default_factory=lambda: {}
    )
    _lagrange_coefficients: Dict[
        MISSING_GUARDIAN_ID, Dict[AVAILABLE_GUARDIAN_ID, ElementModQ]
    ] = field(default_factory=lambda: {})
    """
    A collection of lagrange coefficients `w_{i,j}` computed by available guardians for each missing guardian
    """

    def announce(
        self, guardian: Guardian
    ) -> Optional[Tuple[DecryptionShare, Dict[BALLOT_ID, DecryptionShare]]]:
        """
        Announce that a Guardian is present and participating in the decryption.
        A Decryption Share will be generated for the Guardian

        :param guardian: The guardian who will participate in the decryption.
        :return: decryption shares for tally and ballot for this `Guardian` or `None` if there is an error.
        """

        # Only allow a guardian to announce once
        if guardian.object_id in self._available_guardians:
            log_info(f"guardian {guardian.object_id} already announced")
            return (
                self._tally_shares[guardian.object_id],
                self._ballot_shares[guardian.object_id],
            )

        # Compute the tally and ballot decryption shares
        tally_share = compute_decryption_share(
            guardian, self._ciphertext_tally, self._encryption
        )
        if tally_share is None:
            log_warning(
                f"announce could not generate tally decryption share for {guardian.object_id}"
            )
            return None
        self._tally_shares[guardian.object_id] = tally_share

        # Compute the ballot decryption shares
        ballot_shares = compute_decryption_share_for_ballots(
            guardian, list(self._ciphertext_ballots.values()), self._encryption
        )
        if ballot_shares is None:
            log_warning(
                f"announce could not generate ballot decryption share for {guardian.object_id}"
            )
            return None
        self._ballot_shares[guardian.object_id] = ballot_shares

        # Mark guardian in attendance and check their keys
        self._mark_available(guardian)
        if not self._validate_missing_guardian_keys(guardian):
            return None

        return (tally_share, ballot_shares)

    # pylint: disable=too-many-return-statements
    def get_plaintext_tally(
        self, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> Optional[PlaintextTally]:
        """
        Get the plaintext tally for the election by composing each Guardian's
        decrypted representation of each selection into a decrypted representation

        :return: a `PlaintextTally` or `None`
        """

        # Make sure a Quorum of Guardians have announced
        if len(self._available_guardians) < self._encryption.quorum:
            log_warning(
                "cannot get plaintext tally with less than quorum available guardians"
            )
            return None

        # If all Guardians are present decrypt the tally
        if len(self._available_guardians) == self._encryption.number_of_guardians:
            return decrypt_tally(
                self._ciphertext_tally,
                self._tally_shares,
                self._encryption.crypto_extended_base_hash,
            )

        # If guardians are missing, compensate then decrypt
        self._compute_missing_shares_for_tally(decrypt)

        if len(self._tally_shares) != self._encryption.number_of_guardians:
            log_warning("get plaintext tally failed with share length mismatch")
            return None

        return decrypt_tally(
            self._ciphertext_tally,
            self._tally_shares,
            self._encryption.crypto_extended_base_hash,
        )

    def _mark_available(self, guardian: Guardian) -> None:
        """
        This guardian removes itself from the
        missing list since it generated a valid share
        """
        self._available_guardians[guardian.object_id] = guardian
        if guardian.object_id in self._missing_guardians.keys():
            self._missing_guardians.pop(guardian.object_id)

    def _validate_missing_guardian_keys(self, guardian: Guardian) -> bool:
        """
        Check the guardian's collections of keys and ensure the public keys
        match for the missing guardians
        """

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
                if self._missing_guardians[guardian_id] != public_key:
                    log_warning(
                        (
                            f"announce guardian: {guardian.object_id} "
                            f"expected public key mismatch for missing {guardian_id}"
                        )
                    )
                    return False
            else:
                self._missing_guardians[guardian_id] = missing_guardians[guardian_id]
        return True

    def _compute_missing_shares_for_tally(
        self, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> None:
        # If missing guardians compensate for the missing guardians
        missing_tally_shares: Dict[MISSING_GUARDIAN_ID, DecryptionShare] = {}
        for missing_guardian_id, public_key in self._missing_guardians.items():
            if missing_guardian_id in self._tally_shares:
                continue
            self._compute_lagrange_coefficients(missing_guardian_id)
            compensated_shares = self._get_compensated_shares_for_tally(
                missing_guardian_id, decrypt
            )
            if compensated_shares is None:
                log_warning(
                    f"get plaintext tally failed compensating for {missing_guardian_id}"
                )
                return

            missing_decryption_share = reconstruct_decryption_share(
                missing_guardian_id,
                public_key,
                self._ciphertext_tally,
                compensated_shares,
                self._lagrange_coefficients[missing_guardian_id],
            )
            missing_tally_shares[missing_guardian_id] = missing_decryption_share

        if missing_tally_shares is None:
            log_warning(
                "get plaintext tally failed with computing missing decryption shares"
            )
            return

        # Combine all tally shares
        self._tally_shares.update(missing_tally_shares)

    def _get_compensated_shares_for_tally(
        self, missing_guardian_id: str, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> Optional[Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]]:
        """
        Compensate for a missing guardian by reconstructing the share using the available guardians.

        :param missing_guardian_id: the guardian that failed to `announce`.
        :return: a collection of `CompensatedDecryptionShare` generated from all available guardians
                 or `None if there is an error
        """

        compensated_decryptions: Dict[
            AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare
        ] = {}
        # Loop through each of the available guardians
        # and calculate a partial for the missing one
        for (
            available_gaurdian_id,
            available_guardian,
        ) in self._available_guardians.items():
            # Compute the tally decryption shares
            tally_share = compute_compensated_decryption_share(
                available_guardian,
                missing_guardian_id,
                self._ciphertext_tally,
                self._encryption,
                decrypt,
            )
            if tally_share is None:
                log_warning(f"compensation failed for missing: {missing_guardian_id}")
                break
            compensated_decryptions[available_gaurdian_id] = tally_share

        # Verify generated the correct number of partials
        if len(compensated_decryptions) != len(self._available_guardians):
            log_warning(
                f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}"
            )
            return None

        return compensated_decryptions

    def get_plaintext_ballots(
        self, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> Optional[Dict[BALLOT_ID, PlaintextTally]]:
        """
        Get the plaintext spoiled ballots for the election by composing each Guardian's
        decrypted representation of each selection into a decrypted representation

        :return: a Plaintext Spoiled Ballots or `None`
        """

        # Make sure a Quorum of Guardians have announced
        if len(self._available_guardians) < self._encryption.quorum:
            log_warning("cannot decrypt with less than quorum available guardians")
            return None

        # If all Guardians are present decrypt the ballots
        if len(self._available_guardians) == self._encryption.number_of_guardians:
            return decrypt_ballots(
                self._ciphertext_ballots,
                self._ballot_shares,
                self._encryption.crypto_extended_base_hash,
            )

        # If guardians are missing, compensate then decrypt
        for ballot_id in self._ciphertext_ballots.keys():
            self._compute_missing_shares_for_ballot(ballot_id, decrypt)

            if (
                self._count_ballot_shares(ballot_id)
                != self._encryption.number_of_guardians
            ):
                log_warning("get plaintext ballot failed with share length mismatch")
                return None

        return decrypt_ballots(
            self._ciphertext_ballots,
            self._ballot_shares,
            self._encryption.crypto_extended_base_hash,
        )

    def _count_ballot_shares(self, ballot_id: str) -> int:
        count = 0
        for ballot_shares in self._ballot_shares.values():
            if ballot_shares.get(ballot_id):
                count += 1
        return count

    def _compute_missing_shares_for_ballot(
        self, ballot_id: str, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> None:
        """
        Compute the missing decryption shares for all the guardians who are missing
        and add to the shares of the available guardians
        """
        # If missing guardians compensate for the missing guardians
        for missing_guardian_id, public_key in self._missing_guardians.items():
            self._compute_lagrange_coefficients(missing_guardian_id)
            compensated_shares = self._get_compensated_shares_for_ballot(
                ballot_id, missing_guardian_id, decrypt
            )
            if compensated_shares is None:
                log_warning(
                    f"get plaintext ballot failed compensating for {missing_guardian_id}"
                )
                return

            missing_decryption_share = reconstruct_decryption_share_for_ballot(
                missing_guardian_id,
                public_key,
                self._ciphertext_ballots[ballot_id],
                compensated_shares,
                self._lagrange_coefficients[missing_guardian_id],
            )

            self._ballot_shares[missing_guardian_id][
                ballot_id
            ] = missing_decryption_share

    def _get_compensated_shares_for_ballot(
        self,
        ballot_id: str,
        missing_guardian_id: str,
        decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Optional[Dict[AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare]]:
        """
        Compensate for a missing guardian by reconstructing the share using the available guardians.

        :param ballot_id: The id of the ballot to get the share of
        :param missing_guardian_id: the guardian that failed to `announce`.
        :return: a collection of `CompensatedDecryptionShare` generated from all available guardians
                 or `None if there is an error
        """

        compensated_decryptions: Dict[
            AVAILABLE_GUARDIAN_ID, CompensatedDecryptionShare
        ] = {}
        # Loop through each of the available guardians
        # and calculate a partial for the missing one
        for (
            available_gaurdian_id,
            available_guardian,
        ) in self._available_guardians.items():
            # Compute the tally decryption shares
            ballot_share = compute_compensated_decryption_share_for_ballot(
                available_guardian,
                missing_guardian_id,
                self._ciphertext_ballots[ballot_id],
                self._encryption,
                decrypt,
            )
            if ballot_share is None:
                log_warning(f"compensation failed for missing: {missing_guardian_id}")
                break
            compensated_decryptions[available_gaurdian_id] = ballot_share

        # Verify generated the correct number of partials
        if len(compensated_decryptions) != len(self._available_guardians):
            log_warning(
                f"compensate mismatch partial decryptions for missing guardian {missing_guardian_id}"
            )
            return None

        return compensated_decryptions

    def _compute_lagrange_coefficients(self, missing_guardian_id: str) -> None:
        """Compute lagrange coefficients for each of the available guardians"""
        if self._lagrange_coefficients.get(missing_guardian_id):
            return

        lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ] = {}
        for available_guardian in self._available_guardians.values():
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
        self._lagrange_coefficients[missing_guardian_id] = lagrange_coefficients
