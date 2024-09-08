from typing import Optional

from pretiac.client import Client

from command_watcher.channel import BaseChannel
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
        api_endpoint_host: Optional[str] = None,
        api_endpoint_port: Optional[int] = None,
        http_basic_username: Optional[str] = None,
        http_basic_password: Optional[str] = None,
        client_private_key: Optional[str] = None,
        client_certificate: Optional[str] = None,
        ca_certificate: Optional[str] = None,
    ) -> None:
        """
        :param config_file: The path of the configuration file to load.
        :param api_endpoint_host: The domain or the IP address of the API
            endpoint, e. g. ``icinga.example.com``, ``localhost`` or ``127.0.0.1``.
        :param api_endpoint_port: The TCP port of the API endpoint, for example
            ``5665``.
        :param http_basic_username: The name of the API user used in the HTTP basic
            authentification, e. g. ``apiuser``.
        :param http_basic_password: The password of the API user used in the HTTP
            basic authentification, e. g. ``password``.
        :param client_private_key: The file path of the client’s **private RSA
            key**, for example ``/etc/pretiac/api-client.key.pem``.
        :param client_certificate: The file path of the client’s **certificate**,
            for example ``/etc/pretiac/api-client.cert.pem``.
        :param ca_certificate: The file path of the Icinga **CA (Certification
            Authority)**, for example ``/var/lib/icinga2/certs/ca.crt``.
        :param suppress_exception: If set to ``True``, no exceptions are thrown.
        """
        self.service_name = service_name
        self.service_display_name = service_display_name

        self.__client = Client(
            api_endpoint_host=api_endpoint_host,
            api_endpoint_port=api_endpoint_port,
            http_basic_username=http_basic_username,
            http_basic_password=http_basic_password,
            client_private_key=client_private_key,
            client_certificate=client_certificate,
            ca_certificate=ca_certificate,
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
        try:
            self.__client.send_service_check_result(
                service=service_name,
                host=HOSTNAME,
                exit_status=message.status,
                plugin_output=message.message,
                performance_data=message.performance_data,
                display_name=service_display_name,
            )
        except Exception:
            print("sending to icinga failed")
