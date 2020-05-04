from dataclasses import dataclass

from .serializable import Serializable

@dataclass
class ObjectBase(Serializable):

    object_id: str