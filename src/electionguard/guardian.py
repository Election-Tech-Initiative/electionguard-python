# pylint: disable=too-many-public-methods
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, TypeVar

from .auxiliary import (
    AuxiliaryKeyPair,
    AuxiliaryPublicKey,
    AuxiliaryDecrypt,
    AuxiliaryEncrypt,
)
from .ballot import SubmittedBallot
from .decryption import (
    compute_compensated_decryption_share,
    compute_compensated_decryption_share_for_ballot,
    compute_decryption_share,
    compute_decryption_share_for_ballot,
)
from .decryption_share import CompensatedDecryptionShare, DecryptionShare
from .election import CiphertextElectionContext
from .election_polynomial import PUBLIC_COMMITMENT
from .elgamal import elgamal_combine_public_keys
from .group import ElementModQ
from .key_ceremony import (
    CeremonyDetails,
    ELECTION_JOINT_PUBLIC_KEY,
    ELECTION_PUBLIC_KEY,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    generate_rsa_auxiliary_key_pair,
    PublicKeySet,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from .logs import log_warning
from .rsa import rsa_encrypt, rsa_decrypt
from .serializable import Serializable
from .schnorr import SchnorrProof
from .tally import CiphertextTally
from .types import BALLOT_ID, GUARDIAN_ID
from .utils import get_optional


@dataclass
class GuardianRecord(Serializable):
    """
    Published record containing all required information per Guardian
    for Election record used in verification processes
    """

    guardian_id: GUARDIAN_ID
    """Unique identifier of the guardian"""

    sequence_order: int
    """
    Unique sequence order of the guardian indicating the order
    in which the guardian should be processed
    """

    election_public_key: ELECTION_PUBLIC_KEY
    """
    Guardian's election public key for encrypting election objects.
    """

    election_commitments: List[PUBLIC_COMMITMENT]
    """
    Commitment for each coeffficient of the guardians secret polynomial.
    First commitment is and should be identical to election_public_key.
    """

    election_proofs: List[SchnorrProof]
    """
    Proofs for each commitment for each coeffficient of the guardians secret polynomial.
    First proof is the proof for the election_public_key.
    """


def publish_guardian_record(election_public_key: ElectionPublicKey) -> GuardianRecord:
    """
    Published record containing all required information per Guardian
    for Election record used in verification processes

    :param election_public_key: Guardian's election public key
    :return: Guardian's record
    """
    return GuardianRecord(
        election_public_key.owner_id,
        election_public_key.sequence_order,
        election_public_key.key,
        election_public_key.coefficient_commitments,
        election_public_key.coefficient_proofs,
    )


@dataclass(frozen=True)
class PrivateGuardianRecord(Serializable):
    """Unpublishable private record containing information per Guardian"""

    election_keys: ElectionKeyPair
    """Private election Key pair of this guardian"""

    auxiliary_keys: AuxiliaryKeyPair
    """Private auxiliary key pair of this guardian"""

    backups_to_share: Dict[GUARDIAN_ID, ElectionPartialKeyBackup]
    """This guardian's partial key backups that will be shared to other guardians"""

    guardian_auxiliary_public_keys: Dict[GUARDIAN_ID, AuxiliaryPublicKey]
    """Received auxiliary public keys that are shared with this guardian"""

    guardian_election_public_keys: Dict[GUARDIAN_ID, ElectionPublicKey]
    """Received election public keys that are shared with this guardian"""

    guardian_election_partial_key_backups: Dict[GUARDIAN_ID, ElectionPartialKeyBackup]
    """Received partial key backups that are shared with this guardian"""

    guardian_election_partial_key_verifications: Dict[
        GUARDIAN_ID, ElectionPartialKeyVerification
    ]
    """Verifications of other guardian's backups"""


# pylint: disable=too-many-instance-attributes
class Guardian:
    """
    Guardian of election responsible for safeguarding information and decrypting results.
    The first half of the guardian involves the key exchange known as the key ceremony.
    The second half relates to the decryption process.
    """

    id: str
    sequence_order: int  # Cannot be zero
    ceremony_details: CeremonyDetails

    _auxiliary_keys: AuxiliaryKeyPair
    _election_keys: ElectionKeyPair

    _backups_to_share: Dict[GUARDIAN_ID, ElectionPartialKeyBackup]
    """
    The collection of this guardian's partial key backups that will be shared to other guardians
    """

    # From Other Guardians
    _guardian_auxiliary_public_keys: Dict[GUARDIAN_ID, AuxiliaryPublicKey]
    """
    The collection of other guardians' auxiliary public keys that are shared with this guardian
    """

    _guardian_election_public_keys: Dict[GUARDIAN_ID, ElectionPublicKey]
    """
    The collection of other guardians' election public keys that are shared with this guardian
    """

    _guardian_election_partial_key_backups: Dict[GUARDIAN_ID, ElectionPartialKeyBackup]
    """
    The collection of other guardians' partial key backups that are shared with this guardian
    """

    _guardian_election_partial_key_verifications: Dict[
        GUARDIAN_ID, ElectionPartialKeyVerification
    ]
    """
    The collection of other guardians' verifications that they shared their backups correctly
    """

    def __init__(
        self,
        id: str,
        sequence_order: int,
        number_of_guardians: int,
        quorum: int,
        nonce_seed: Optional[ElementModQ] = None,
    ) -> None:
        """
        Initialize a guardian with the specified arguments

        :param id: the unique identifier for the guardian
        :param sequence_order: a unique number in [1, 256) that identifies this guardian
        :param number_of_guardians: the total number of guardians that will participate in the election
        :param quorum: the count of guardians necessary to decrypt
        :param nonce_seed: an optional `ElementModQ` value that can be used to generate the `ElectionKeyPair`.
                           It is recommended to only use this field for testing.
        """
        self.id = id
        self.sequence_order = sequence_order
        self.set_ceremony_details(number_of_guardians, quorum)
        self._backups_to_share = {}
        self._guardian_auxiliary_public_keys = {}
        self._guardian_election_public_keys = {}
        self._guardian_election_partial_key_backups = {}
        self._guardian_election_partial_key_verifications = {}

        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair(nonce_seed if nonce_seed is not None else None)

    def reset(self, number_of_guardians: int, quorum: int) -> None:
        """
        Reset guardian to initial state
        :param number_of_guardians: Number of guardians in election
        :param quorum: Quorum of guardians required to decrypt
        """
        self._backups_to_share.clear()
        self._guardian_auxiliary_public_keys.clear()
        self._guardian_election_public_keys.clear()
        self._guardian_election_partial_key_backups.clear()
        self._guardian_election_partial_key_verifications.clear()
        self.set_ceremony_details(number_of_guardians, quorum)
        self.generate_auxiliary_key_pair()
        self.generate_election_key_pair()

    def publish(self) -> GuardianRecord:
        """Publish record of guardian with all required information"""
        return publish_guardian_record(self._election_keys.share())

    def export_private_data(self) -> PrivateGuardianRecord:
        """Export private data of guardian. Warning cannot be published"""
        return PrivateGuardianRecord(
            self._election_keys,
            self._auxiliary_keys,
            self._backups_to_share,
            self._guardian_auxiliary_public_keys,
            self._guardian_election_public_keys,
            self._guardian_election_partial_key_backups,
            self._guardian_election_partial_key_verifications,
        )

    def set_ceremony_details(self, number_of_guardians: int, quorum: int) -> None:
        """
        Set ceremony details for election
        :param number_of_guardians: Number of guardians in election
        :param quorum: Quorum of guardians required to decrypt
        """
        self.ceremony_details = CeremonyDetails(number_of_guardians, quorum)

    # Public Keys
    def share_public_keys(self) -> PublicKeySet:
        """
        Share public election and auxiliary keys for guardian
        :return: Public set of election and auxiliary keys
        """
        return PublicKeySet(
            self._election_keys.share(),
            self._auxiliary_keys.share(),
        )

    def save_guardian_public_keys(self, public_key_set: PublicKeySet) -> None:
        """
        Save public election and auxiliary keys for another guardian
        :param public_key_set: Public set of election and auxiliary keys
        """
        self.save_auxiliary_public_key(public_key_set.auxiliary)
        self.save_election_public_key(public_key_set.election)

    def all_public_keys_received(self) -> bool:
        """
        True if all election and auxiliary public keys have been received.
        :return: All election and auxiliary public keys backups received
        """
        return (
            self.all_auxiliary_public_keys_received()
            and self.all_election_public_keys_received()
        )

    def generate_auxiliary_key_pair(
        self,
        generate_auxiliary_key_pair: Callable[
            [GUARDIAN_ID, int], AuxiliaryKeyPair
        ] = generate_rsa_auxiliary_key_pair,
    ) -> None:
        """
        Generate auxiliary key pair
        :param generate_auxiliary_key_pair: Function to generate auxiliary key pair
        """
        self._auxiliary_keys = generate_auxiliary_key_pair(self.id, self.sequence_order)
        self.save_auxiliary_public_key(self.share_auxiliary_public_key())

    def share_auxiliary_public_key(self) -> AuxiliaryPublicKey:
        """
        Share auxiliary public key with another guardian
        :return: Auxiliary Public Key
        """
        return self._auxiliary_keys.share()

    def save_auxiliary_public_key(self, key: AuxiliaryPublicKey) -> None:
        """
        Save a guardians auxiliary public key
        :param key: Auxiliary public key
        """
        self._guardian_auxiliary_public_keys[key.owner_id] = key

    def all_auxiliary_public_keys_received(self) -> bool:
        """
        True if all auxiliary public keys have been received.
        :return: All auxiliary public keys backups received
        """
        return (
            len(self._guardian_auxiliary_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def generate_election_key_pair(self, nonce: ElementModQ = None) -> None:
        """
        Generate election key pair for encrypting/decrypting election
        """
        self._election_keys = generate_election_key_pair(
            self.id, self.sequence_order, self.ceremony_details.quorum, nonce
        )
        self.save_election_public_key(self.share_election_public_key())

    def share_election_public_key(self) -> ElectionPublicKey:
        """
        Share election public key with another guardian
        :return: Election public key
        """
        return self._election_keys.share()

    def save_election_public_key(self, key: ElectionPublicKey) -> None:
        """
        Save a guardians election public key
        :param key: Election public key
        """
        self._guardian_election_public_keys[key.owner_id] = key

    def all_election_public_keys_received(self) -> bool:
        """
        True if all election public keys have been received.
        :return: All election public keys backups received
        """
        return (
            len(self._guardian_election_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def generate_election_partial_key_backups(
        self, encrypt: AuxiliaryEncrypt = rsa_encrypt
    ) -> bool:
        """
        Generate all election partial key backups based on existing public keys
        :param encrypt: Encryption function using auxiliary key
        """
        if not self.all_auxiliary_public_keys_received():
            log_warning(
                f"guardian; {self.id} could not generate election partial key backups: missing auxiliary keys"
            )
            return False
        for auxiliary_key in self._guardian_auxiliary_public_keys.values():
            backup = generate_election_partial_key_backup(
                self.id, self._election_keys.polynomial, auxiliary_key, encrypt
            )
            if backup is None:
                log_warning(
                    f"guardian; {self.id} could not generate election partial key backups: failed to encrypt"
                )
                return False
            self._backups_to_share[auxiliary_key.owner_id] = backup

        return True

    # Election Partial Key Backup
    def share_election_partial_key_backup(
        self, designated_id: GUARDIAN_ID
    ) -> Optional[ElectionPartialKeyBackup]:
        """
        Share election partial key backup with another guardian
        :param designated_id: Designated guardian
        :return: Election partial key backup or None
        """
        return self._backups_to_share.get(designated_id)

    def share_election_partial_key_backups(self) -> List[ElectionPartialKeyBackup]:
        """
        Share all election partial key backups
        :return: Election partial key backup or None
        """
        return list(self._backups_to_share.values())

    def save_election_partial_key_backup(
        self, backup: ElectionPartialKeyBackup
    ) -> None:
        """
        Save election partial key backup from another guardian
        :param backup: Election partial key backup
        """
        self._guardian_election_partial_key_backups[backup.owner_id] = backup

    def all_election_partial_key_backups_received(self) -> bool:
        """
        True if all election partial key backups have been received.
        :return: All election partial key backups received
        """
        return (
            len(self._guardian_election_partial_key_backups)
            == self.ceremony_details.number_of_guardians - 1
        )

    # Verification
    def verify_election_partial_key_backup(
        self,
        guardian_id: GUARDIAN_ID,
        decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Optional[ElectionPartialKeyVerification]:
        """
        Verify election partial key backup value is in polynomial
        :param guardian_id: Owner of backup to verify
        :param decrypt:
        :return: Election partial key verification or None
        """
        backup = self._guardian_election_partial_key_backups.get(guardian_id)
        public_key = self._guardian_election_public_keys.get(guardian_id)
        if backup is None or public_key is None:
            return None
        return verify_election_partial_key_backup(
            self.id, backup, public_key, self._auxiliary_keys, decrypt
        )

    def publish_election_backup_challenge(
        self, guardian_id: GUARDIAN_ID
    ) -> Optional[ElectionPartialKeyChallenge]:
        """
        Publish election backup challenge of election partial key verification
        :param guardian_id: Owner of election key
        :return: Election partial key challenge or None
        """
        backup_in_question = self._backups_to_share.get(guardian_id)
        if backup_in_question is None:
            return None
        return generate_election_partial_key_challenge(
            backup_in_question, self._election_keys.polynomial
        )

    def verify_election_partial_key_challenge(
        self, challenge: ElectionPartialKeyChallenge
    ) -> ElectionPartialKeyVerification:
        """
        Verify challenge of previous verification of election partial key
        :param challenge: Election partial key challenge
        :return: Election partial key verification
        """
        return verify_election_partial_key_challenge(self.id, challenge)

    def save_election_partial_key_verification(
        self, verification: ElectionPartialKeyVerification
    ) -> None:
        """
        Save election partial key verification from another guardian
        :param verification: Election partial key verification
        """
        self._guardian_election_partial_key_verifications[
            verification.designated_id
        ] = verification

    def all_election_partial_key_backups_verified(self) -> bool:
        """
        True if all election partial key backups have been verified.
        :return: All election partial key backups verified
        """
        required = self.ceremony_details.number_of_guardians - 1
        if len(self._guardian_election_partial_key_verifications) != required:
            return False
        for verification in self._guardian_election_partial_key_verifications.values():
            if not verification.verified:
                return False
        return True

    # Joint Key
    def publish_joint_key(self) -> Optional[ELECTION_JOINT_PUBLIC_KEY]:
        """
        Creates the joint election key from the public keys of all guardians
        :return: Optional joint key for election
        """
        if not self.all_election_public_keys_received():
            return None
        if not self.all_election_partial_key_backups_verified():
            return None

        public_keys = map(
            lambda public_key: public_key.key,
            self._guardian_election_public_keys.values(),
        )
        return elgamal_combine_public_keys(public_keys)

    def share_other_guardian_key(self, guardian_id: GUARDIAN_ID) -> ElectionPublicKey:
        """Share other guardians keys shared during key ceremony"""
        return get_optional(self._guardian_election_public_keys.get(guardian_id))

    def compute_tally_share(
        self, tally: CiphertextTally, context: CiphertextElectionContext
    ) -> Optional[DecryptionShare]:
        """
        Compute the decryption share of tally

        :param tally: Ciphertext tally to get share of
        :param context: Election context
        :return: Decryption share of tally or None if failure
        """
        return compute_decryption_share(
            self._election_keys,
            tally,
            context,
        )

    def compute_ballot_shares(
        self, ballots: List[SubmittedBallot], context: CiphertextElectionContext
    ) -> Dict[BALLOT_ID, Optional[DecryptionShare]]:
        """
        Compute the decryption shares of ballots

        :param ballots: List of ciphertext ballots to get shares of
        :param context: Election context
        :return: Decryption shares of ballots or None if failure
        """
        shares = {}
        for ballot in ballots:
            share = compute_decryption_share_for_ballot(
                self._election_keys,
                ballot,
                context,
            )
            shares[ballot.object_id] = share
        return shares

    def compute_compensated_tally_share(
        self,
        missing_guardian_id: GUARDIAN_ID,
        tally: CiphertextTally,
        context: CiphertextElectionContext,
        decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Optional[CompensatedDecryptionShare]:
        """
        Compute the compensated decryption share of a tally for a missing guardian

        :param missing_guardian_id: Missing guardians id
        :param tally: Ciphertext tally to get share of
        :param context: Election context
        :param decrypt: Auxiliary decrypt method
        :return: Compensated decryption share of tally or None if failure
        """
        # Ensure missing guardian information available
        missing_guardian_key = self._guardian_election_public_keys.get(
            missing_guardian_id
        )
        missing_guardian_backup = self._guardian_election_partial_key_backups.get(
            missing_guardian_id
        )
        if missing_guardian_key is None or missing_guardian_backup is None:
            return None
        return compute_compensated_decryption_share(
            self.share_election_public_key(),
            self._auxiliary_keys,
            missing_guardian_key,
            missing_guardian_backup,
            tally,
            context,
            decrypt,
        )

    def compute_compensated_ballot_shares(
        self,
        missing_guardian_id: GUARDIAN_ID,
        ballots: List[SubmittedBallot],
        context: CiphertextElectionContext,
        decrypt: AuxiliaryDecrypt = rsa_decrypt,
    ) -> Dict[BALLOT_ID, Optional[CompensatedDecryptionShare]]:
        """
        Compute the compensated decryption share of each ballots for a missing guardian

        :param missing_guardian_id: Missing guardians id
        :param ballots: List of ciphertext ballots to get shares of
        :param context: Election context
        :param decrypt: Auxiliary decrypt method
        :return: Compensated decryption shares of ballots or None if failure
        """
        shares: Dict[BALLOT_ID, Optional[CompensatedDecryptionShare]] = {
            ballot.object_id: None for ballot in ballots
        }
        # Ensure missing guardian information available
        missing_guardian_key = self._guardian_election_public_keys.get(
            missing_guardian_id
        )
        missing_guardian_backup = self._guardian_election_partial_key_backups.get(
            missing_guardian_id
        )
        if missing_guardian_key is None or missing_guardian_backup is None:
            return shares

        for ballot in ballots:
            share = compute_compensated_decryption_share_for_ballot(
                self.share_election_public_key(),
                self._auxiliary_keys,
                missing_guardian_key,
                missing_guardian_backup,
                ballot,
                context,
                decrypt,
            )
            shares[ballot.object_id] = share
        return shares


_SHARE = TypeVar("_SHARE")


def get_valid_ballot_shares(
    ballot_shares: Dict[BALLOT_ID, Optional[_SHARE]]
) -> Dict[BALLOT_ID, _SHARE]:
    filtered_shares = {}
    for ballot_id, ballot_share in ballot_shares.items():
        if ballot_share is not None:
            filtered_shares[ballot_id] = ballot_share
    return filtered_shares
