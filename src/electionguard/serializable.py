from pydantic import BaseModel, PrivateAttr

Private = PrivateAttr


class Serializable(BaseModel):
    """Serializable data object intended for exporting and importing"""

    class Config:
        """Model config to handle private properties"""

        underscore_attrs_are_private = True
