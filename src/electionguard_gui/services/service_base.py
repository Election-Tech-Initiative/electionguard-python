from abc import ABC


class ServiceBase(ABC):
    """Responsible for common functionality among services"""

    def init(self) -> None:
        self.expose()

    def expose(self) -> None:
        pass
