import os
import pwd
import socket
import textwrap
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, TypedDict

from typing_extensions import Unpack

if TYPE_CHECKING:
    from . import Process

HOSTNAME = socket.gethostname()
USERNAME = pwd.getpwuid(os.getuid()).pw_name

Status = Literal[0, 1, 2, 3]


class MinimalMessageParams(TypedDict, total=False):
    custom_message: str
    """Custom message"""

    prefix: str
    """ Prefix of the report message."""

    body: str
    """ A longer report text."""

    performance_data: Dict[str, Any]
    """ A dictionary like
          `{'perf_1': 1, 'perf_2': 'test'}`"""


class MessageParams(MinimalMessageParams, total=False):
    status: Status
    """ 0 (OK), 1 (WARNING), 2 (CRITICAL), 3 (UNKOWN): see
          Nagios / Icinga monitoring status / state."""

    service_name: str
    """The name of the service."""

    service_display_name: str
    """The human readable version of a service name."""

    log_records: str
    """Log records separated by new lines"""

    processes: List["Process"]


class BaseClass:
    def _obj_to_str(self, attributes: List[str] = []) -> str:
        if not attributes:
            attributes = dir(self)
        output: List[str] = []
        for attribute in attributes:
            if not attribute.startswith("_") and not callable(getattr(self, attribute)):
                value = getattr(self, attribute)
                if value:
                    value = textwrap.shorten(str(value), width=64)
                    value = value.replace("\n", " ")
                    output.append("{}: '{}'".format(attribute, value))
        return "[{}] {}".format(self.__class__.__name__, ", ".join(output))


class Message(BaseClass):
    """
    This message class bundles all available message data into an object. The
    different reporters can choose which data they use.
    """

    _data: MessageParams

    def __init__(self, **data: Unpack[MessageParams]) -> None:
        self._data = data

    def __str__(self) -> str:
        return self._obj_to_str()

    @property
    def status(self) -> Literal[0, 1, 2, 3]:
        """0 (OK), 1 (WARNING), 2 (CRITICAL), 3 (UNKOWN): see
        Nagios / Icinga monitoring status / state."""
        return self._data.get("status", 0)

    @property
    def status_text(self) -> str:
        """The status as a text word like `OK`."""
        if self.status == 0:
            return "OK"
        elif self.status == 1:
            return "WARNING"
        elif self.status == 2:
            return "CRITICAL"
        else:
            return "UNKNOWN"

    @property
    def service_name(self) -> str:
        return self._data.get("service_name", "service_not_set")

    @property
    def service_display_name(self) -> str | None:
        return self._data.get("service_display_name", None)

    @property
    def performance_data(self) -> str:
        """
        :return: A concatenated string
        """
        performance_data = self._data.get("performance_data")
        if performance_data:
            pairs: List[str] = []
            key: str
            value: Any
            for key, value in performance_data.items():
                pairs.append("{!s}={!s}".format(key, value))
            return " ".join(pairs)
        return ""

    @property
    def custom_message(self) -> str:
        return self._data.get("custom_message", "")

    @property
    def prefix(self) -> str:
        return self._data.get("prefix", "[cwatcher]:")

    @property
    def message(self) -> str:
        output: List[str] = []
        if self.prefix:
            output.append(self.prefix)

        output.append(self.service_name.upper())
        output.append(self.status_text)
        if self.custom_message:
            output.append("- {}".format(self.custom_message))
        return " ".join(output)

    @property
    def message_monitoring(self) -> str:
        """message + performance_data"""
        output: List[str] = []
        output.append(self.message)
        if self.performance_data:
            output.append("|")
            output.append(self.performance_data)
        return " ".join(output)

    @property
    def body(self) -> str:
        """Text body for the e-mail message."""
        output: List[str] = []
        output.append("Host: {}".format(HOSTNAME))
        output.append("User: {}".format(USERNAME))
        output.append("Service name: {}".format(self.service_name))

        if self.performance_data:
            output.append("Performance data: {}".format(self.performance_data))

        body: str = self._data.get("body", "")
        if body:
            output.append("")
            output.append(body)

        log_records = self._data.get("log_records", "")
        if log_records:
            output.append("")
            output.append("Log records:")
            output.append("")
            output.append(log_records)

        return "\n".join(output)

    @property
    def processes(self) -> Optional[str]:
        output: List[str] = []
        processes = self._data.get("processes")
        if processes:
            for process in processes:
                output.append(" ".join(process.args_normalized))
        if output:
            return "({})".format("; ".join(output))
        return None

    @property
    def user(self) -> str:
        return "[user:{}]".format(USERNAME)
