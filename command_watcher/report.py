import abc
import os
import pwd
import shutil
import socket
import subprocess
import textwrap
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypedDict

from typing_extensions import Unpack

from . import icinga
from .email import send_email

if TYPE_CHECKING:
    from . import Process

HOSTNAME = socket.gethostname()
USERNAME = pwd.getpwuid(os.getuid()).pw_name

Status = Literal[0, 1, 2, 3]


class BaseClass:

    def _obj_to_str(self, attributes: List[str] = []) -> str:
        if not attributes:
            attributes = dir(self)
        output: List[str] = []
        for attribute in attributes:
            if not attribute.startswith('_') and \
               not callable(getattr(self, attribute)):
                value = getattr(self, attribute)
                if value:
                    value = textwrap.shorten(str(value), width=64)
                    value = value.replace('\n', ' ')
                    output.append('{}: \'{}\''.format(attribute, value))
        return '[{}] {}'.format(self.__class__.__name__, ', '.join(output))


class MinimalMessageParams(TypedDict, total=False):

    custom_message: str
    """Custom message"""

    prefix: str
    """ Prefix of the report message."""

    body: str
    """ A longer report text."""

    preformance_data: Dict[str, Any]
    """ A dictionary like
          `{'perf_1': 1, 'perf_2': 'test'}`"""


class MessageParams(MinimalMessageParams, total=False):

    status: Status
    """ 0 (OK), 1 (WARNING), 2 (CRITICAL), 3 (UNKOWN): see
          Nagios / Icinga monitoring status / state."""

    service_name: str
    """The name of the service."""

    log_records: str
    """Log records separated by new lines"""

    processes: List['Process']


class Message(BaseClass):
    """
    This message class bundles all available message data into an object. The
    different reporters can choose which data they use.
    """

    _data: MessageParams

    def __init__(self, **data: Unpack[MessageParams]):
        self._data = data

    def __str__(self):
        return self._obj_to_str()

    @property
    def status(self) -> int:
        """0 (OK), 1 (WARNING), 2 (CRITICAL), 3 (UNKOWN): see
        Nagios / Icinga monitoring status / state."""
        return self._data.get('status', 0)

    @property
    def status_text(self) -> str:
        """The status as a text word like `OK`."""
        return icinga.States[self.status]

    @property
    def service_name(self) -> str:
        return self._data.get('service_name', 'service_not_set')

    @property
    def performance_data(self) -> str:
        """
        :return: A concatenated string
        :rtype: str
        """
        performance_data = self._data.get('performance_data')
        if performance_data and isinstance(performance_data, dict):
            pairs: List[str] = []
            key: str
            value: Any
            for key, value in performance_data.items():
                pairs.append('{!s}={!s}'.format(key, value))
            return ' '.join(pairs)
        return ''

    @property
    def custom_message(self) -> str:
        return self._data.get('custom_message', '')

    @property
    def prefix(self) -> str:
        return self._data.get('prefix', '[cwatcher]:')

    @property
    def message(self) -> str:
        output: List[str] = []
        if self.prefix:
            output.append(self.prefix)

        output.append(self.service_name.upper())
        output.append(self.status_text)
        if self.custom_message:
            output.append('- {}'.format(self.custom_message))
        return ' '.join(output)

    @property
    def message_monitoring(self) -> str:
        """message + performance_data"""
        output: List[str] = []
        output.append(self.message)
        if self.performance_data:
            output.append('|')
            output.append(self.performance_data)
        return ' '.join(output)

    @property
    def body(self) -> str:
        """Text body for the e-mail message."""
        output: List[str] = []
        output.append('Host: {}'.format(HOSTNAME))
        output.append('User: {}'.format(USERNAME))
        output.append('Service name: {}'.format(self.service_name))

        if self.performance_data:
            output.append('Performance data: {}'.format(self.performance_data))

        body: str = self._data.get('body', '')
        if body:
            output.append('')
            output.append(body)

        log_records = self._data.get('log_records', '')
        if log_records:
            output.append('')
            output.append('Log records:')
            output.append('')
            output.append(log_records)

        return '\n'.join(output)

    @property
    def processes(self) -> Optional[str]:
        output: List[str] = []
        processes = self._data.get('processes')
        if processes:
            for process in processes:
                output.append(' '.join(process.args_normalized))
        if output:
            return'({})'.format('; '.join(output))

    @property
    def user(self) -> str:
        return '[user:{}]'.format(USERNAME)


class BaseChannel(BaseClass, metaclass=abc.ABCMeta):
    """Base class for all reporters"""

    @abc.abstractmethod
    def report(self, message: Message) -> None:
        raise NotImplementedError('A reporter class must have a `report` '
                                  'method.')


class EmailChannel(BaseChannel):
    """Send reports by e-mail."""

    def __init__(self, smtp_server: str, smtp_login: str, smtp_password: str,
                 to_addr: str, from_addr: str = '',
                 to_addr_critical: str = ''):
        self.smtp_server = smtp_server
        self.smtp_login = smtp_login
        self.smtp_password = smtp_password
        self.to_addr = to_addr
        self.from_addr = from_addr
        if not from_addr:
            self.from_addr = '{0} <{1}@{0}>'.format(HOSTNAME, USERNAME)
        self.to_addr_critical = to_addr_critical

    def __str__(self) -> str:
        return self._obj_to_str(['smtp_server', 'smtp_login', 'to_addr',
                                 'from_addr', ])

    def report(self, message: Message) -> None:
        """Send an e-mail message.

        :param message: A message object.
        """
        if message.status == 2 and self.to_addr_critical:
            to_addr = self.to_addr_critical
        else:
            to_addr = self.to_addr

        send_email(
            from_addr=self.from_addr,
            to_addr=to_addr,
            subject=message.message,
            body=message.body,
            smtp_login=self.smtp_login,
            smtp_password=self.smtp_password,
            smtp_server=self.smtp_server
        )


class IcingaChannel(BaseChannel):
    url: str
    user: str
    password: str
    service_name: str

    def __init__(self, url: str, user: str, password: str,
                 service_name: str):
        self.url = url
        self.user = user
        self.password = password
        self.service_name = service_name

    def __str__(self) -> str:
        # No password!
        return self._obj_to_str(['url', 'user', 'service_name'])

    def report(self, message: Message) -> None:
        icinga.send_passive_check(
            url=self.url,
            user=self.user,
            password=self.password,
            status=message.status,
            host_name=HOSTNAME,
            service_name=message.service_name,
            text_output=message.message,
            performance_data=message.performance_data
        )


class BeepChannel(BaseChannel):
    """Send beep sounds."""

    def __init__(self):
        self.cmd = shutil.which('beep')

    def __str__(self) -> str:
        # No password!
        return self._obj_to_str(['cmd'])

    def beep(self, frequency: float = 4186.01, length: float = 50) -> None:
        """
        Generate a beep sound using the “beep” command.

        * A success tone: frequency=4186.01, length=40
        * A failure tone: frequency=65.4064, length=100

        :param frequency: Frequency in Hz.
        :param length: Length in milliseconds.
        """
        # TODO: Use self.cmd -> Fix tests
        subprocess.run(['beep', '-f', str(float(frequency)), '-l',
                        str(float(length))])

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

    def __init__(self):
        self.channels = []

    def add_channel(self, channel: BaseChannel) -> None:
        self.channels.append(channel)

    def report(self, **data: Unpack[MessageParams]) -> Message:
        message = Message(**data)
        for channel in self.channels:
            channel.report(message)
        return message


reporter = Reporter()
