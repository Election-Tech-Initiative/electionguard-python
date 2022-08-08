# pylint: disable=too-many-public-methods

from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar

from electionguard.utils import get_optional

from .ballot import SubmittedBallot
from .decryption import (
    compute_compensated_decryption_share,
    compute_compensated_decryption_share_for_ballot,
    compute_decryption_share,
    compute_decryption_share_for_ballot,
    decrypt_backup,
)
from .decryption_share import CompensatedDecryptionShare, DecryptionShare
from .election import CiphertextElectionContext
from .election_polynomial import ElectionPolynomial, PublicCommitment
from .elgamal import ElGamalKeyPair, ElGamalPublicKey, elgamal_combine_public_keys
from .group import ElementModP, ElementModQ
from .key_ceremony import (
    CeremonyDetails,
    ElectionKeyPair,
    ElectionPartialKeyBackup,
    ElectionPartialKeyChallenge,
    ElectionPartialKeyVerification,
    ElectionPublicKey,
    generate_election_key_pair,
    generate_election_partial_key_backup,
    generate_election_partial_key_challenge,
    verify_election_partial_key_backup,
    verify_election_partial_key_challenge,
)
from .logs import log_warning
from .schnorr import SchnorrProof
from .tally import CiphertextTally
from .type import BallotId, GuardianId


@dataclass
class GuardianRecord:
    """
    Published record containing all required information per Guardian
    for Election record used in verification processes
    """

    guardian_id: GuardianId
    """Unique identifier of the guardian"""

    sequence_order: int
    """
    Unique sequence order of the guardian indicating the order
    in which the guardian should be processed
    """

    election_public_key: ElGamalPublicKey
    """
    Guardian's election public key for encrypting election objects.
    """

    election_commitments: List[PublicCommitment]
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


@dataclass
class PrivateGuardianRecord:
    """Unpublishable private record containing information per Guardian."""

    guardian_id: GuardianId
    """Unique identifier of the guardian"""

    election_keys: ElectionKeyPair
    """Private election Key pair of this guardian"""

    backups_to_share: Dict[GuardianId, ElectionPartialKeyBackup]
    """This guardian's partial key backups that will be shared to other guardians"""

    guardian_election_public_keys: Dict[GuardianId, ElectionPublicKey]
    """Received election public keys that are shared with this guardian"""

    guardian_election_partial_key_backups: Dict[GuardianId, ElectionPartialKeyBackup]
    """Received partial key backups that are shared with this guardian"""

    guardian_election_partial_key_verifications: Dict[
        GuardianId, ElectionPartialKeyVerification
    ]
    """Verifications of other guardian's backups"""


class Guardian:
    """
    Guardian of election responsible for safeguarding information and decrypting results.

    The first half of the guardian involves the key exchange known as the key ceremony.
    The second half relates to the decryption process.
    """

    _election_keys: ElectionKeyPair
    ceremony_details: CeremonyDetails

    _backups_to_share: Dict[GuardianId, ElectionPartialKeyBackup]
    """
    The collection of this guardian's partial key backups that will be shared to other guardians
    """

    # From Other Guardians
    _guardian_election_public_keys: Dict[GuardianId, ElectionPublicKey]
    """
    The collection of other guardians' election public keys that are shared with this guardian
    """

    _guardian_election_partial_key_backups: Dict[GuardianId, ElectionPartialKeyBackup]
    """
    The collection of other guardians' partial key backups that are shared with this guardian
    """

    _guardian_election_partial_key_verifications: Dict[
        GuardianId, ElectionPartialKeyVerification
    ]
    """
    The collection of other guardians' verifications that they shared their backups correctly
    """

    def __init__(
        self,
        key_pair: ElectionKeyPair,
        ceremony_details: CeremonyDetails,
        election_public_keys: Dict[GuardianId, ElectionPublicKey] = None,
        partial_key_backups: Dict[GuardianId, ElectionPartialKeyBackup] = None,
        backups_to_share: Dict[GuardianId, ElectionPartialKeyBackup] = None,
        guardian_election_partial_key_verifications: Dict[
            GuardianId, ElectionPartialKeyVerification
        ] = None,
    ) -> None:
        """
        Initialize a guardian with the specified arguments.

        :param key_pair The key pair the guardian generated during a key ceremony
        :param ceremony_details The details of the key ceremony
        :param election_public_keys the public keys the guardian generated during a key ceremony
        :param partial_key_backups the partial key backups the guardian generated during a key ceremony
        """

        self._election_keys = key_pair
        self.ceremony_details = ceremony_details

        # Reduce this ⬇️
        self._backups_to_share = {} if backups_to_share is None else backups_to_share
        self._guardian_election_public_keys = (
            {} if election_public_keys is None else election_public_keys
        )
        self._guardian_election_partial_key_backups = (
            {} if partial_key_backups is None else partial_key_backups
        )
        self._guardian_election_partial_key_verifications = (
            {}
            if guardian_election_partial_key_verifications is None
            else guardian_election_partial_key_verifications
        )

        self.save_guardian_key(key_pair.share())

    @property
    def id(self) -> GuardianId:
        return self._election_keys.owner_id

    @property
    def sequence_order(self) -> int:
        return self._election_keys.sequence_order

    @classmethod
    def from_public_key(
        cls,
        number_of_guardians: int,
        quorum: int,
        public_key: ElectionPublicKey,
    ) -> "Guardian":
        el_gamal_key_pair = ElGamalKeyPair(ElementModQ(0), public_key.key)
        election_key_pair = ElectionKeyPair(
            public_key.owner_id,
            public_key.sequence_order,
            el_gamal_key_pair,
            ElectionPolynomial([]),
        )
        ceremony_details = CeremonyDetails(number_of_guardians, quorum)
        return cls(election_key_pair, ceremony_details)

    @classmethod
    def from_nonce(
        cls,
        id: str,
        sequence_order: int,
        number_of_guardians: int,
        quorum: int,
        nonce: ElementModQ = None,
    ) -> "Guardian":
        """Creates a guardian with an `ElementModQ` value that will be used to generate
        the `ElectionKeyPair`. If no nonce provided, this will be generated automatically.
        This method should generally only be used for testing."""
        key_pair = generate_election_key_pair(id, sequence_order, quorum, nonce)
        ceremony_details = CeremonyDetails(number_of_guardians, quorum)
        return cls(key_pair, ceremony_details)

    @classmethod
    def from_private_record(
        cls,
        private_guardian_record: PrivateGuardianRecord,
        number_of_guardians: int,
        quorum: int,
    ) -> "Guardian":
        guardian = cls(
            private_guardian_record.election_keys,
            CeremonyDetails(number_of_guardians, quorum),
            private_guardian_record.guardian_election_public_keys,
            private_guardian_record.guardian_election_partial_key_backups,
            private_guardian_record.backups_to_share,
            private_guardian_record.guardian_election_partial_key_verifications,
        )

        return guardian

    def publish(self) -> GuardianRecord:
        """Publish record of guardian with all required information."""
        return publish_guardian_record(self._election_keys.share())

    def export_private_data(self) -> PrivateGuardianRecord:
        """Export private data of guardian. Warning cannot be published."""
        return PrivateGuardianRecord(
            self.id,
            self._election_keys,
            self._backups_to_share,
            self._guardian_election_public_keys,
            self._guardian_election_partial_key_backups,
            self._guardian_election_partial_key_verifications,
        )

    def set_ceremony_details(self, number_of_guardians: int, quorum: int) -> None:
        """
        Set ceremony details for election.

        :param number_of_guardians: Number of guardians in election
        :param quorum: Quorum of guardians required to decrypt
        """
        self.ceremony_details = CeremonyDetails(number_of_guardians, quorum)

    def decrypt_backup(self, backup: ElectionPartialKeyBackup) -> Optional[ElementModQ]:
        """
        Decrypts a compensated partial decryption of an elgamal encryption
        on behalf of a missing guardian.

        :param backup: An encrypted backup from a missing guardian.
        :return: A decrypted backup.
        """

        return decrypt_backup(get_optional(backup), self._election_keys)

    # Public Keys
    def share_key(self) -> ElectionPublicKey:
        """
        Share election public key with another guardian.

        :return: Election public key
        """
        return self._election_keys.share()

    def save_guardian_key(self, key: ElectionPublicKey) -> None:
        """
        Save public election keys for another guardian.

        :param key: Election public key
        """
        self._guardian_election_public_keys[key.owner_id] = key

    def all_guardian_keys_received(self) -> bool:
        """
        True if all keys have been received.

        :return: All keys backups received
        """
        return (
            len(self._guardian_election_public_keys)
            == self.ceremony_details.number_of_guardians
        )

    def generate_election_partial_key_backups(self) -> bool:
        """
        Generate all election partial key backups based on existing public keys.
        """
        for guardian_key in self._guardian_election_public_keys.values():
            backup = generate_election_partial_key_backup(
                self.id, self._election_keys.polynomial, guardian_key
            )
            if backup is None:
                log_warning(
                    f"guardian; {self.id} could not generate election partial key backups: failed to encrypt"
                )
                return False
            self._backups_to_share[guardian_key.owner_id] = backup

        return True

    # Election Partial Key Backup
    def share_election_partial_key_backup(
        self, designated_id: GuardianId
    ) -> Optional[ElectionPartialKeyBackup]:
        """
        Share election partial key backup with another guardian.

        :param designated_id: Designated guardian
        :return: Election partial key backup or None
        """
        return self._backups_to_share.get(designated_id)

    def share_election_partial_key_backups(self) -> List[ElectionPartialKeyBackup]:
        """
        Share all election partial key backups.

        :return: Election partial key backup or None
        """
        return list(self._backups_to_share.values())

    def save_election_partial_key_backup(
        self, backup: ElectionPartialKeyBackup
    ) -> None:
        """
        Save election partial key backup from another guardian.

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
        guardian_id: GuardianId,
    ) -> Optional[ElectionPartialKeyVerification]:
        """
        Verify election partial key backup value is in polynomial.

        :param guardian_id: Owner of backup to verify
        :param decrypt:
        :return: Election partial key verification or None
        """
        backup = self._guardian_election_partial_key_backups.get(guardian_id)
        public_key = self._guardian_election_public_keys.get(guardian_id)
        if backup is None:
            raise ValueError(f"No backup exists for {guardian_id}")
        if public_key is None:
            raise ValueError(f"No public key exists for {guardian_id}")
        return verify_election_partial_key_backup(
            self.id, backup, public_key, self._election_keys
        )

    def publish_election_backup_challenge(
        self, guardian_id: GuardianId
    ) -> Optional[ElectionPartialKeyChallenge]:
        """
        Publish election backup challenge of election partial key verification.

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
        Verify challenge of previous verification of election partial key.

        :param challenge: Election partial key challenge
        :return: Election partial key verification
        """
        return verify_election_partial_key_challenge(self.id, challenge)

    def save_election_partial_key_verification(
        self, verification: ElectionPartialKeyVerification
    ) -> None:
        """
        Save election partial key verification from another guardian.

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
    def publish_joint_key(self) -> Optional[ElementModP]:
        """
        Create the joint election key from the public keys of all guardians.

        :return: Optional joint key for election
        """
        if not self.all_guardian_keys_received():
            return None
        if not self.all_election_partial_key_backups_verified():
            return None

        public_keys = map(
            lambda public_key: public_key.key,
            self._guardian_election_public_keys.values(),
        )
        return elgamal_combine_public_keys(public_keys)

    def share_other_guardian_key(
        self, guardian_id: GuardianId
    ) -> Optional[ElectionPublicKey]:
        """Share other guardians keys shared during key ceremony"""
        return self._guardian_election_public_keys.get(guardian_id)

    def compute_tally_share(
        self, tally: CiphertextTally, context: CiphertextElectionContext
    ) -> Optional[DecryptionShare]:
        """
        Compute the decryption share of tally.

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
    ) -> Dict[BallotId, Optional[DecryptionShare]]:
        """
        Compute the decryption shares of ballots.

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
        missing_guardian_id: GuardianId,
        tally: CiphertextTally,
        context: CiphertextElectionContext,
    ) -> Optional[CompensatedDecryptionShare]:
        """
        Compute the compensated decryption share of a tally for a missing guardian.

        :param missing_guardian_id: Missing guardians id
        :param tally: Ciphertext tally to get share of
        :param context: Election context
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
        missing_guardian_coordinate = self.decrypt_backup(missing_guardian_backup)
        return compute_compensated_decryption_share(
            get_optional(missing_guardian_coordinate),
            self.share_key(),
            missing_guardian_key,
            tally,
            context,
        )

    def compute_compensated_ballot_shares(
        self,
        missing_guardian_id: GuardianId,
        ballots: List[SubmittedBallot],
        context: CiphertextElectionContext,
    ) -> Dict[BallotId, Optional[CompensatedDecryptionShare]]:
        """
        Compute the compensated decryption share of each ballots for a missing guardian.

        :param missing_guardian_id: Missing guardians id
        :param ballots: List of ciphertext ballots to get shares of
        :param context: Election context
        :return: Compensated decryption shares of ballots or None if failure
        """
        shares: Dict[BallotId, Optional[CompensatedDecryptionShare]] = {
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

        missing_guardian_coordinate = self.decrypt_backup(missing_guardian_backup)
        for ballot in ballots:
            share = compute_compensated_decryption_share_for_ballot(
                get_optional(missing_guardian_coordinate),
                missing_guardian_key,
                self.share_key(),
                ballot,
                context,
            )
            shares[ballot.object_id] = share
        return shares


_SHARE = TypeVar("_SHARE")


def get_valid_ballot_shares(
    ballot_shares: Dict[BallotId, Optional[_SHARE]]
) -> Dict[BallotId, _SHARE]:
    """Get valid ballot shares."""
    filtered_shares = {}
    for ballot_id, ballot_share in ballot_shares.items():
        if ballot_share is not None:
            filtered_shares[ballot_id] = ballot_share
    return filtered_shares
