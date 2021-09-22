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
    # importlib.metadata is present in Python 3.8 and later
    import importlib.metadata as import_lib_metadata
except ImportError:
    # use the shim package importlib-metadata pre-3.8
    import importlib_metadata as import_lib_metadata  # type: ignore[no-redef]

try:
    __version__ = import_lib_metadata.version(__package__.split("_", maxsplit=1)[0])
except import_lib_metadata.PackageNotFoundError:
    __version__ = "0.0.0"
