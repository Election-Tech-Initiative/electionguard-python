from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .election import (
    CiphertextElectionContext,
    ElectionDescription,
    InternalElectionDescription,
    make_ciphertext_election_context,
)
from .group import ElementModP
from .utils import get_optional


@dataclass
class ElectionBuilder(object):
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
    The quorum of guardians necessary to decrypt an election.  Must be less than `number_of_guardians`
    """

    description: ElectionDescription

    internal_description: InternalElectionDescription = field(init=False)

    elgamal_public_key: Optional[ElementModP] = field(default=None)

    def __post_init__(self) -> None:
        self.internal_description = InternalElectionDescription(self.description)

    def set_public_key(self, elgamal_public_key: ElementModP) -> ElectionBuilder:
        """
        Set election public key
        :param elgamal_public_key: elgamal public key for election
        :return: election builder
        """
        self.elgamal_public_key = elgamal_public_key
        return self

    def build(
        self,
    ) -> Optional[Tuple[InternalElectionDescription, CiphertextElectionContext]]:
        """
        Build election
        :return: election description and context or none
        """
        if not self.description.is_valid():
            return None

        if self.elgamal_public_key is None:
            return None

        return (
            self.internal_description,
            make_ciphertext_election_context(
                self.number_of_guardians,
                self.quorum,
                get_optional(self.elgamal_public_key),
                self.description.crypto_hash(),
            ),
        )
