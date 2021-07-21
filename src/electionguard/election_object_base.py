from dataclasses import dataclass


@dataclass
class ElectionObjectBase:
    """A base object to derive other election objects identifiable by object_id."""

    object_id: str
