from typing import List, Literal

from typing_extensions import Unpack

from command_watcher.channels.base_channel import BaseChannel
from command_watcher.message import Message, MessageParams

Status = Literal[0, 1, 2, 3]


class Reporter:
    """Collect all channels."""

    channels: List[BaseChannel]

    def __init__(self) -> None:
        self.channels = []

    def add_channel(self, channel: BaseChannel) -> None:
        self.channels.append(channel)

    def report(self, **data: Unpack[MessageParams]) -> Message:
        message = Message(**data)
        for channel in self.channels:
            channel.report(message)
        return message


reporter: Reporter = Reporter()
