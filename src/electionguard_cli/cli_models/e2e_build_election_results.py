from electionguard.election import CiphertextElectionContext
from electionguard.manifest import InternalManifest


class BuildElectionResults:
    """The results of building an election, more specifically an internal manifest and context."""

    def __init__(
        self, internal_manifest: InternalManifest, context: CiphertextElectionContext
    ):
        self.internal_manifest = internal_manifest
        self.context = context

    internal_manifest: InternalManifest
    context: CiphertextElectionContext
