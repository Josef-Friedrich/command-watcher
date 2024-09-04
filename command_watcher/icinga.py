from typing import Literal, Optional

from pretiac import get_default_client

client = get_default_client()


def send_service_check_result(
    service: str,
    host: str,
    exit_status: Literal[0, 1, 2, 3],
    plugin_output: Optional[str],
    performance_data: Optional[str],
    service_display_name: Optional[str],
) -> None:
    client.send_service_check_result(
        service=service,
        host=host,
        exit_status=exit_status,
        plugin_output=plugin_output,
        performance_data=performance_data,
        display_name=service_display_name,
    )
