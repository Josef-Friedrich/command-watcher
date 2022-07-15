from typing import Literal, Optional

import urllib3
from icinga2apic.client import Client

urllib3.disable_warnings()  # type: ignore


STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

States = {
    STATE_OK: 'OK',
    STATE_WARNING: 'WARNING',
    STATE_CRITICAL: 'CRITICAL',
    STATE_UNKNOWN: 'UNKNOWN',
}


def send_passive_check(url: str, user: str, password: str,
                       status: Literal[0, 1, 2, 3],
                       host_name: str, service_name: str,
                       text_output: str,
                       performance_data: Optional[str] = None
                       ):
    """
    https://icinga.com/docs/icinga-2/latest/doc/12-icinga2-api/#process-check-result
    """
    client = Client(url=url,
                    username=user, password=password)
    return client.actions.process_check_result(
        object_type='Service',
        name='{}!{}'.format(host_name, service_name),
        exit_status=status,
        plugin_output=text_output, performance_data=performance_data)
