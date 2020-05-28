from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple

from .election import (
    CiphertextElectionContext,
    ElectionDescription,
    InternalElectionDescription,
)

from .group import ElementModP
from .utils import get_optional


@dataclass
class ElectionBuilder(object):
    """
    `ElectionBuilder` is a stateful builder object that constructs `CiphertextElectionContext` objects
    following the initialization process that ElectionGuard Expects.
    """

    number_trustees: int
    threshold_trustees: int

    description: ElectionDescription

    internal_description: InternalElectionDescription = field(init=False)

    elgamal_public_key: Optional[ElementModP] = field(default=None)

    def __post_init__(self) -> None:
        self.internal_description = InternalElectionDescription(self.description)

    def set_public_key(self, elgamal_public_key: ElementModP) -> ElectionBuilder:
        self.elgamal_public_key = elgamal_public_key
        return self

    def build(
        self,
    ) -> Optional[Tuple[InternalElectionDescription, CiphertextElectionContext]]:

        if not self.description.is_valid():
            return None

        if self.elgamal_public_key is None:
            return None

        return (
            self.internal_description,
            CiphertextElectionContext(
                self.number_trustees,
                self.threshold_trustees,
                get_optional(self.elgamal_public_key),
                self.description.crypto_hash(),
            ),
        )
