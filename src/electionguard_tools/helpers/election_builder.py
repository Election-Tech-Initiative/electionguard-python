from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from electionguard.elgamal import ElGamalPublicKey

from electionguard.election import (
    CiphertextElectionContext,
    make_ciphertext_election_context,
)
from electionguard.group import ElementModQ
from electionguard.manifest import Manifest, InternalManifest
from electionguard.utils import get_optional


@dataclass
class ElectionBuilder:
    """
    `ElectionBuilder` is a stateful builder object that constructs `CiphertextElectionContext` objects
    following the initialization process that ElectionGuard Expects.
    """

    number_of_guardians: int
    """
    The number of guardians necessary to generate the public key
    """
    quorum: int
    """
    The quorum of guardians necessary to decrypt an election.  Must be fewer than `number_of_guardians`
    """

    manifest: Manifest

    internal_manifest: InternalManifest = field(init=False)

    election_key: Optional[ElGamalPublicKey] = field(default=None)

    commitment_hash: Optional[ElementModQ] = field(default=None)

    extended_data: Optional[Dict[str, str]] = field(default=None)

    def __post_init__(self) -> None:
        self.internal_manifest = InternalManifest(self.manifest)

    def set_public_key(
        self, election_joint_public_key: ElGamalPublicKey
    ) -> ElectionBuilder:
        """
        Set election public key
        :param election_joint_public_key: elgamal public key for election
        :return: election builder
        """
        self.election_key = election_joint_public_key
        return self

    def set_commitment_hash(self, commitment_hash: ElementModQ) -> ElectionBuilder:
        """
        Set commitment hash
        :param commitment_hash: hash of the commitments guardians make to each other
        :return: election builder
        """
        self.commitment_hash = commitment_hash
        return self

    def add_extended_data_field(self, name: str, value: str) -> ElectionBuilder:
        """
        Set extended data field
        :param name: name of the extended data entry to add
        :param value: value of the extended data entry
        """
        if self.extended_data is None:
            self.extended_data = {}
        self.extended_data[name] = value
        return self

    def build(
        self,
    ) -> Optional[Tuple[InternalManifest, CiphertextElectionContext]]:
        """
        Build election
        :return: election manifest and context or none
        """
        if not self.manifest.is_valid():
            return None

        if self.election_key is None:
            return None

        return (
            self.internal_manifest,
            make_ciphertext_election_context(
                self.number_of_guardians,
                self.quorum,
                get_optional(self.election_key),
                get_optional(self.commitment_hash),
                self.manifest.crypto_hash(),
                extended_data=self.extended_data,
            ),
        )
