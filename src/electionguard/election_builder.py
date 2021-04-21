from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from electionguard.key_ceremony import ELECTION_JOINT_PUBLIC_KEY

from .election import CiphertextElectionContext, make_ciphertext_election_context
from .group import ElementModQ
from .manifest import Manifest, InternalManifest
from .utils import get_optional


@dataclass
class ElectionBuilder:
    """
    `ElectionBuilder` is a stateful builder object that constructs `CiphertextElectionContext` objects
    following the initialization process that ElectionGuard Expects.
    SUGGESTION Perhaps move to test package.
    """

    number_of_guardians: int
    """
    The number of guardians necessary to generate the public key
    """
    quorum: int
    """
    The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    """

    manifest: Manifest

    internal_manifest: InternalManifest = field(init=False)

    election_joint_public_key: Optional[ELECTION_JOINT_PUBLIC_KEY] = field(default=None)

    commitment_hash: Optional[ElementModQ] = field(default=None)

    def __post_init__(self) -> None:
        self.internal_manifest = InternalManifest(self.manifest)

    def set_public_key(
        self, election_joint_public_key: ELECTION_JOINT_PUBLIC_KEY
    ) -> ElectionBuilder:
        """
        Set election public key
        :param election_joint_public_key: elgamal public key for election
        :return: election builder
        """
        self.election_joint_public_key = election_joint_public_key
        return self

    def set_commitment_hash(self, commitment_hash: ElementModQ) -> ElectionBuilder:
        """
        Set commitment hash
        :param commitment_hash: hash of the commitments guardians make to each other
        :return: election builder
        """
        self.commitment_hash = commitment_hash
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

        if self.election_joint_public_key is None:
            return None

        return (
            self.internal_manifest,
            make_ciphertext_election_context(
                self.number_of_guardians,
                self.quorum,
                get_optional(self.election_joint_public_key),
                get_optional(self.commitment_hash),
                self.manifest.crypto_hash(),
            ),
        )
