import importlib.metadata

# <AUTOGEN_INIT>
from electionguard_verify import verify

from electionguard_verify.verify import (
    Verification,
    verify_ballot,
)

__all__ = ["Verification", "verify", "verify_ballot"]

# </AUTOGEN_INIT>

# single source version from pyproject.toml
try:
    __version__ = importlib.metadata.version(__package__.split("_", maxsplit=1)[0])
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"
