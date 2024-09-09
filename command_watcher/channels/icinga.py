from typing import Optional

from pretiac.client import Client
from pretiac.config import Config

from command_watcher.channels.base_channel import BaseChannel
from command_watcher.message import Message
from command_watcher.utils import HOSTNAME


class IcingaChannel(BaseChannel):
    service_name: str

    service_display_name: Optional[str]

    __client: Client

    api_endpoint_host: Optional[str]
    api_endpoint_port: Optional[int]
    http_basic_username: Optional[str]
    client_certificate: Optional[str]
    client_private_key: Optional[str]
    ca_certificate: Optional[str]

    def __init__(
        self,
        service_name: str,
        config: Config,
        service_display_name: Optional[str] = None,
    ) -> None:
        self.service_name = service_name
        self.service_display_name = service_display_name
        self.__client = Client(
            config=config,
            config_file=False,
        )
        self.api_endpoint_host = config.api_endpoint_host
        self.api_endpoint_port = config.api_endpoint_port
        self.http_basic_username = config.http_basic_username
        self.client_certificate = config.client_certificate
        self.client_private_key = config.client_private_key
        self.ca_certificate = config.ca_certificate

    def __str__(self) -> str:
        return self._obj_to_str(
            [
                "api_endpoint_host",
                "api_endpoint_port",
                "http_basic_username",
                "client_certificate",
                "client_private_key",
                "ca_certificate",
            ]
        )

    def report(self, message: Message) -> None:
        service_name = (
            message.service_name if message.service_name else self.service_name
        )
        service_display_name = (
            message.service_display_name
            if message.service_display_name
            else self.service_display_name
        )
        self.__client.send_service_check_result(
            service=service_name,
            host=HOSTNAME,
            exit_status=message.status,
            plugin_output=message.message,
            performance_data=message.performance_data,
            display_name=service_display_name,
        )
