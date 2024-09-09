import abc

from command_watcher.message import BaseClass, Message


class BaseChannel(BaseClass, metaclass=abc.ABCMeta):
    """Base class for all reporters"""

    @abc.abstractmethod
    def report(self, message: Message) -> None:
        raise NotImplementedError("A reporter class must have a `report` " "method.")
