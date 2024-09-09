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

    def __init__(
        self,
        service_name: str,
        service_display_name: Optional[str] = None,
        config: Optional[Config] = None,
    ) -> None:
        self.service_name = service_name
        self.service_display_name = service_display_name
        self.__client = Client(
            config=config,
            config_file=False,
        )

    def __str__(self) -> str:
        return "external configured icinga2 api client"

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
