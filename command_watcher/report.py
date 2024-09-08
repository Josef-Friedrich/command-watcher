import shutil
import subprocess
from typing import List, Literal, Union

from typing_extensions import Unpack

from command_watcher.channel import BaseChannel
from command_watcher.message import Message, MessageParams

Status = Literal[0, 1, 2, 3]


class BeepChannel(BaseChannel):
    """Send beep sounds."""

    cmd: Union[str, None]

    def __init__(self) -> None:
        self.cmd = shutil.which("beep")

    def __str__(self) -> str:
        # No password!
        return self._obj_to_str(["cmd"])

    def beep(self, frequency: float = 4186.01, length: float = 50) -> None:
        """
        Generate a beep sound using the “beep” command.

        * A success tone: frequency=4186.01, length=40
        * A failure tone: frequency=65.4064, length=100

        :param frequency: Frequency in Hz.
        :param length: Length in milliseconds.
        """
        # TODO: Use self.cmd -> Fix tests
        subprocess.run(["beep", "-f", str(float(frequency)), "-l", str(float(length))])

    def report(self, message: Message) -> None:
        """Send a beep sounds.

        :param message: A message object. The only attribute that takes an
          effect is the status attribute (0-3).
        """
        if message.status == 0:  # OK
            self.beep(frequency=4186.01, length=50)  # C8 (highest note)
        elif message.status == 1:  # WARNING
            self.beep(frequency=261.626, length=100)  # C4 (middle C)
        elif message.status == 2:  # CRITICAL
            self.beep(frequency=65.4064, length=150)  # C2 (low C)
        elif message.status == 3:  # UNKOWN
            self.beep(frequency=32.7032, length=200)  # C1


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
