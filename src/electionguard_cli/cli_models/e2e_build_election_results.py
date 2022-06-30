from dataclasses import dataclass

from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest


@dataclass
class BuildElectionResults:
    """The results of building an election, more specifically an internal manifest and context."""

    internal_manifest: InternalManifest
    context: CiphertextElectionContext
