from dataclasses import dataclass, field
from typing import Dict, Optional, List

from .auxiliary import AuxiliaryDecrypt
from .data_store import DataStore
from .decryption import (
    compute_decryption_share,
    compute_compensated_decryption_share,
    reconstruct_missing_tally_decryption_shares,
)
from .decryption_share import TallyDecryptionShare, CompensatedTallyDecryptionShare
from .decrypt_with_shares import decrypt_tally
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

    _available_guardians: Dict[AVAILABLE_GUARDIAN_ID, Guardian] = field(
        default_factory=lambda: {}
    )
    _missing_guardians: DataStore[MISSING_GUARDIAN_ID, ElectionPublicKey] = field(
        default_factory=lambda: DataStore()
    )

    _decryption_shares: Dict[AVAILABLE_GUARDIAN_ID, TallyDecryptionShare] = field(
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
        MISSING_GUARDIAN_ID,
        Dict[AVAILABLE_GUARDIAN_ID, CompensatedTallyDecryptionShare],
    ] = field(default_factory=lambda: {})
    """
    A collection of Compensated Decryption Shares for each Available Guardian
    """

    def announce(self, guardian: Guardian) -> Optional[TallyDecryptionShare]:
        """
        Announce that a Guardian is present and participating in the decryption.  
        A Decryption Share will be generated for the Guardian

        :param guardian: The guardian who will participate in the decryption.
        :return: a `TallyDecryptionShare` for this `Guardian` or `None` if there is an error.
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
        self, missing_guardian_id: str, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> Optional[List[CompensatedTallyDecryptionShare]]:
        """
        Compensate for a missing guardian by reconstructing the share using the available guardians.

        :param missing_guardian_id: the guardian that failed to `announce`.
        :return: a collection of `CompensatedTallyDecryptionShare` generated from all available guardians
                 or `None if there is an error
        """

        # Only allow a guardian to be compensated for once
        if missing_guardian_id in self._compensated_decryption_shares:
            log_warning(f"guardian {missing_guardian_id} already compensated")
            return list(
                self._compensated_decryption_shares[missing_guardian_id].values()
            )

        compensated_decryptions: List[CompensatedTallyDecryptionShare] = []
        lagrange_coefficients: Dict[AVAILABLE_GUARDIAN_ID, ElementModQ] = {}

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
                decrypt,
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

    def get_plaintext_tally(
        self, recompute: bool = False, decrypt: AuxiliaryDecrypt = rsa_decrypt
    ) -> Optional[PlaintextTally]:
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
            return decrypt_tally(
                self._ciphertext_tally, self._decryption_shares, self._encryption
            )

        # If missing guardians compensate for the missing guardians
        for missing in self._missing_guardians.keys():
            compensated_decryptions = self.compensate(missing, decrypt)
            if compensated_decryptions is None:
                log_warning(f"get plaintext tally failed compensating for {missing}")
                return None

        # Reconstruct the missing partial decryptions from the compensation shares
        missing_decryption_shares = reconstruct_missing_tally_decryption_shares(
            self._ciphertext_tally,
            self._missing_guardians,
            self._compensated_decryption_shares,
            self._lagrange_coefficients,
        )
        if missing_decryption_shares is None or len(missing_decryption_shares) != len(
            self._missing_guardians
        ):
            log_warning(f"get plaintext tally failed with missing decryption shares")
            return None

        merged_decryption_shares: Dict[str, TallyDecryptionShare] = {}

        for available, share in self._decryption_shares.items():
            merged_decryption_shares[available] = share

        for missing, share in missing_decryption_shares.items():
            merged_decryption_shares[missing] = share

        if len(merged_decryption_shares) != self._encryption.number_of_guardians:
            log_warning(f"get plaintext tally failed with share length mismatch")
            return None

        return decrypt_tally(
            self._ciphertext_tally, merged_decryption_shares, self._encryption
        )

    def _submit_decryption_share(self, share: TallyDecryptionShare) -> bool:
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
        self, shares: List[CompensatedTallyDecryptionShare]
    ) -> bool:
        """
        Submit compensated decryption shares to be used in the decryption
        """
        results = [self._submit_compensated_decryption_share(share) for share in shares]
        return all(results)

    def _submit_compensated_decryption_share(
        self, share: CompensatedTallyDecryptionShare
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
