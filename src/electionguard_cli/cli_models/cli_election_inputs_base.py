from abc import ABC
from typing import List
from electionguard.guardian import Guardian
from electionguard.manifest import Manifest


class CliElectionInputsBase(ABC):
    """Responsible for holding inputs common to all CLI election commands"""

    guardian_count: int
    quorum: int
    manifest: Manifest
    guardians: List[Guardian]
