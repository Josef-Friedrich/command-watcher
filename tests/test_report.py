from typing import Any
from unittest import mock

import command_watcher
from command_watcher import Message
from command_watcher.report import Status
from command_watcher.utils import HOSTNAME, USERNAME


class TestClassMessage:
    def setup_method(self) -> None:
        process_1 = command_watcher.Process("ls")
        process_2 = command_watcher.Process(["ls", "-a"])
        self.message = Message(
            status=0,
            service_name="service",
            performance_data={"value1": 1, "value2": 2},
            custom_message="Everything ok",
            processes=[process_1, process_2],
            body="A long body text.",
            log_records="1 OK \n2 Warning",
        )

    def test_property_status(self) -> None:
        assert self.message.status == 0

    def test_property_status_not_set(self) -> None:
        message = Message()
        assert message.status == 0
        assert message.status_text == "OK"

    def test_property_status_text(self) -> None:
        assert self.message.status_text == "OK"

    def test_property_service_name_not_set(self) -> None:
        message = Message()
        assert message.service_name == "service_not_set"

    def test_property_performance_data(self) -> None:
        assert self.message.performance_data == "value1=1 value2=2"

    def test_property_prefix(self) -> None:
        assert self.message.prefix == "[cwatcher]:"

    def test_property_message(self) -> None:
        assert self.message.message == "[cwatcher]: SERVICE OK - Everything ok"

    def test_property_message_monitoring(self) -> None:
        assert (
            self.message.message_monitoring
            == "[cwatcher]: SERVICE OK - Everything ok | value1=1 value2=2"
        )

    def test_property_body(self) -> None:
        body = (
            "Host: {}\n"
            "User: {}\n"
            "Service name: service\n"
            "Performance data: value1=1 value2=2\n\n"
            "A long body text.\n\nLog records:\n\n1 OK \n2 Warning"
        )
        assert self.message.body == body.format(HOSTNAME, USERNAME)

    def test_property_processes(self) -> None:
        assert self.message.processes == "(ls; ls -a)"


class TestClassEmailChannel:
    def setup_method(self) -> None:
        self.email = command_watcher.EmailChannel(
            smtp_server="mail.example.com:587",
            smtp_login="jf",
            smtp_password="123",
            to_addr="logs@example.com",
            from_addr="from@example.com",
            to_addr_critical="critical@example.com",
        )

    def test_attribute_smtp_server(self) -> None:
        assert self.email.smtp_server == "mail.example.com:587"

    def test_attribute_smtp_login(self) -> None:
        assert self.email.smtp_login == "jf"

    def test_attribute_smtp_password(self) -> None:
        assert self.email.smtp_password == "123"

    def test_attribute_to_addr(self) -> None:
        assert self.email.to_addr == "logs@example.com"

    def test_attribute_from_addr(self) -> None:
        assert self.email.from_addr == "from@example.com"

    def test_attribute_to_addr_critical(self) -> None:
        assert self.email.to_addr_critical == "critical@example.com"

    def test_magic_method_str(self) -> None:
        self.maxDiff = None
        assert (
            str(self.email) == "[EmailChannel] smtp_server: 'mail.example.com:587', "
            "smtp_login: 'jf', to_addr: 'logs@example.com', "
            "from_addr: 'from@example.com'"
        )

    def test_method_report(self) -> None:
        message = Message(status=0, service_name="test", body="body")
        with mock.patch("command_watcher.report.send_email") as send_email:
            self.email.report(message)
        send_email.assert_called_with(
            body="Host: {}\nUser: {}\nService name: test\n\nbody".format(
                HOSTNAME, USERNAME
            ),
            from_addr="from@example.com",
            smtp_login="jf",
            smtp_password="123",
            smtp_server="mail.example.com:587",
            subject="[cwatcher]: TEST OK",
            to_addr="logs@example.com",
        )

    def test_method_report_critical(self) -> None:
        message = Message(status=2, service_name="test", body="body")
        with mock.patch("command_watcher.report.send_email") as send_email:
            self.email.report(message)
        send_email.assert_called_with(
            body="Host: {}\nUser: {}\nService name: test\n\nbody".format(
                HOSTNAME, USERNAME
            ),
            from_addr="from@example.com",
            smtp_login="jf",
            smtp_password="123",
            smtp_server="mail.example.com:587",
            subject="[cwatcher]: TEST CRITICAL",
            to_addr="critical@example.com",
        )


class TestClassIcingaChannel:
    icinga: command_watcher.IcingaChannel

    def setup_method(self) -> None:
        self.icinga = command_watcher.IcingaChannel(service_name="Service")

    def assert_called_with(
        self, mock: mock.Mock, status: int, text_output: str, performance_data: str
    ) -> None:
        mock.assert_called_with(
            service="my_service",
            host=HOSTNAME,
            exit_status=status,
            plugin_output=text_output,
            performance_data=performance_data,
            service_display_name=None,
        )

    def send_passive_check(self, **kwargs: Any) -> mock.MagicMock | mock.AsyncMock:
        message = Message(service_name="my_service", prefix="", **kwargs)
        with mock.patch(
            "command_watcher.report.send_service_check_result"
        ) as send_service_check_result:
            self.icinga.report(message)
        return send_service_check_result

    def test_property_service_name(self) -> None:
        assert self.icinga.service_name == "Service"

    def test_magic_method_str(self) -> None:
        assert str(self.icinga) == "external configured icinga2 api client"

    def test_method_send_passive_check(self) -> None:
        send_passive_check = self.send_passive_check(
            status=3,
            custom_message="text",
            performance_data={"perf_1": 1, "perf_2": "lol"},
        )
        self.assert_called_with(
            send_passive_check, 3, "MY_SERVICE UNKNOWN - text", "perf_1=1 perf_2=lol"
        )

    def test_method_send_passive_check_kwargs(self) -> None:
        send_passive_check = self.send_passive_check(
            status=3,
            custom_message="text",
            performance_data={"perf_1": 1, "perf_2": "lol"},
        )
        self.assert_called_with(
            send_passive_check, 3, "MY_SERVICE UNKNOWN - text", "perf_1=1 perf_2=lol"
        )

    def test_method_send_passive_check_without_custom_output(self) -> None:
        send_passive_check = self.send_passive_check(
            status=0, performance_data={"perf_1": 1, "perf_2": "lol"}
        )
        self.assert_called_with(
            send_passive_check, 0, "MY_SERVICE OK", "perf_1=1 perf_2=lol"
        )

    def test_method_send_passive_check_without_custom_output_kwargs(self) -> None:
        send_passive_check = self.send_passive_check(
            status=0, performance_data={"perf_1": 1, "perf_2": "lol"}
        )
        self.assert_called_with(
            send_passive_check, 0, "MY_SERVICE OK", "perf_1=1 perf_2=lol"
        )


class TestClassBeepChannel:
    def setup_method(self) -> None:
        self.beep = command_watcher.BeepChannel()

    def report(self, status: Status) -> mock.MagicMock | mock.AsyncMock:
        message = Message(service_name="my_service", prefix="", status=status)
        with mock.patch("subprocess.run") as subprocess_run:
            self.beep.report(message)
        return subprocess_run

    def test_status_ok(self) -> None:
        subprocess_run = self.report(0)
        subprocess_run.assert_called_with(["beep", "-f", "4186.01", "-l", "50.0"])

    def test_status_warning(self) -> None:
        subprocess_run = self.report(1)
        subprocess_run.assert_called_with(["beep", "-f", "261.626", "-l", "100.0"])

    def test_status_critical(self) -> None:
        subprocess_run = self.report(2)
        subprocess_run.assert_called_with(["beep", "-f", "65.4064", "-l", "150.0"])

    def test_status_unkown(self) -> None:
        subprocess_run = self.report(3)
        subprocess_run.assert_called_with(["beep", "-f", "32.7032", "-l", "200.0"])
