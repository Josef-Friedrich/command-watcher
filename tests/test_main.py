import os
from typing import Any
from unittest import mock

import pytest
from stdout_stderr_capturing import Capturing

import command_watcher
from command_watcher import CommandExecutor, Watch
from command_watcher.message import Message
from command_watcher.utils import HOSTNAME, USERNAME
from tests.helper import CONF, DIR_FILES


class TestClassCommandExecutor:
    cmd_stderr = DIR_FILES / "stderr.sh"

    cmd_stdout = DIR_FILES / "stdout.sh"

    def test_attribute_args(self) -> None:
        process = CommandExecutor("ls -l")
        assert process.args == "ls -l"

    def test_property_args_normalized(self) -> None:
        process = CommandExecutor("ls -l")
        assert process.args_normalized == ["ls", "-l"]

    def test_property_stdout(self) -> None:
        process = CommandExecutor(self.cmd_stdout)
        assert process.stdout

    def test_property_line_count_stdout(self) -> None:
        process = CommandExecutor(self.cmd_stdout)
        assert process.line_count_stdout == 1
        assert process.line_count_stderr == 0

    def test_property_stderr(self) -> None:
        process = CommandExecutor(self.cmd_stderr)
        assert process.stderr

    def test_property_line_count_stderr(self) -> None:
        process = CommandExecutor(self.cmd_stderr)
        assert process.line_count_stdout == 0
        assert process.line_count_stderr == 1


class TestClassWatch:
    def setup_method(self) -> None:
        self.cmd_stderr = os.path.join(DIR_FILES, "stderr.sh")
        self.cmd_stdout = os.path.join(DIR_FILES, "stdout.sh")

    def test_argument_config_file(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        assert isinstance(watch._config.email.to_addr, str)  # type: ignore

    def test_method_run_output_stdout(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        with Capturing() as output:
            process = watch.run(self.cmd_stdout)
        assert process.subprocess.returncode == 0
        assert len(output) == 3
        assert "STDOUT" in output[1]
        assert "One line to stdout!" in output[1]
        assert "Execution time: " in output[2]

    def test_method_run_output_stderr(self) -> None:
        watch = Watch(
            config_file=CONF,
            service_name="test",
            raise_exceptions=False,
        )
        with Capturing(stream="stderr") as output:
            process = watch.run(self.cmd_stderr)
        assert process.subprocess.returncode == 1
        # On travis
        # ['Exception in thread Thread-59:', 'Trace[993 chars][0m'] != ''
        # self.assertEqual(len(output), 1)
        assert "STDERR" in output.tostring()
        assert "One line to stderr!" in output.tostring()

    def test_method_run_multiple(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        watch.run(self.cmd_stdout)
        watch.run(self.cmd_stderr)
        assert len(watch._log_handler.buffer) == 9  # type: ignore
        assert "Hostname: " in watch._log_handler.all_records  # type: ignore

    def test_method_run_log_true(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        process = watch.run(self.cmd_stdout, log=True)
        assert watch.stdout == "One line to stdout!"
        assert process.stdout == "One line to stdout!"

    def test_method_run_log_false(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        process = watch.run(self.cmd_stdout, log=False)
        assert watch.stdout == ""
        assert process.stdout == "One line to stdout!"

    def test_method_run_kwargs(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        with mock.patch("subprocess.Popen") as Popen:
            process = Popen.return_value
            process.stdout = b""
            process.stderr = b""
            process.returncode = 0
            watch.run("ls", cwd="/")
        Popen.assert_called_with(["ls"], cwd="/", stderr=-1, stdout=-1)

    def test_method_run_kwargs_exception(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        with pytest.raises(TypeError):
            watch.run("ls", xxx=False)  # type: ignore

    def test_property_service_name(self) -> None:
        watch = Watch(config_file=CONF, service_name="Service")
        assert watch._service_name == "Service"  # type: ignore

    def test_property_hostname(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        assert watch._hostname == HOSTNAME  # type: ignore

    def test_property_stdout(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        watch.log.stdout("stdout")
        assert watch.stdout == "stdout"

    def test_property_stderr(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        watch.log.stderr("stderr")
        assert watch.stderr == "stderr"

    def test_propertyprocesses(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        assert watch.processes == []
        watch.run(["ls"])
        watch.run(["ls", "-l"])
        watch.run(["ls", "-la"])
        assert len(watch.processes) == 3

    @pytest.mark.skip
    def test_method_report_channel_email(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        watch.log.info("info")
        watch.run("ls")

        with mock.patch("command_watcher.report.send_service_check_result"), mock.patch(
            "smtplib.SMTP"
        ) as SMTP:
            watch.report(
                status=0,
                custom_message="My message",
                performance_data={"perf_1": 1, "perf_2": "test"},
                prefix="",
            )

        SMTP.assert_called_with("smtp.example.com:587")
        server = SMTP.return_value
        server.login.assert_called_with("Login", "Password")
        call_args = server.sendmail.call_args[0]
        assert call_args[0] == "from@example.com"
        assert call_args[1] == ["to@example.com"]
        assert "From: from@example.com\nTo: to@example.com\n" in call_args[2]

    @pytest.mark.skip
    def test_method_report_channel_email_critical(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        with mock.patch("command_watcher.channels.icinga.IcingaChannel"), mock.patch(
            "command_watcher.channels.email.SMTP"
        ) as SMTP:
            watch.report(status=2)
        server = SMTP.return_value
        call_args = server.sendmail.call_args[0]
        assert call_args[1] == ["critical@example.com"]
        assert "From: from@example.com\nTo: critical@example.com\n" in call_args[2]

    @pytest.mark.skip
    def test_method_report_channel_nsca(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        with mock.patch(
            "command_watcher.channels.icinga.Client"
        ) as send_service_check_result, mock.patch(
            "command_watcher.channels.email.SMTP"
        ):
            watch.report(
                status=0,
                custom_message="My message",
                performance_data={"perf_1": 1, "perf_2": "test"},
                prefix="",
            )
        send_service_check_result.assert_called_with(
            service="my_service",
            host=HOSTNAME,
            exit_status=0,
            plugin_output="MY_SERVICE OK - My message",
            performance_data="perf_1=1 perf_2=test",
            service_display_name=None,
        )

        records = watch._log_handler.all_records  # type: ignore
        assert "DEBUG [Message]" in records
        assert "custom_message: 'My message'," in records
        assert "message: 'MY_SERVICE OK - My message'," in records
        assert (
            "message_monitoring: 'MY_SERVICE OK - My message | "
            "perf_1=1 perf_2=test'," in records
        )
        assert "performance_data: 'perf_1=1 perf_2=test'" in records
        assert "service_name: 'my_service'," in records
        assert "status_text: 'OK'," in records
        assert "user: '[user:{}]'".format(USERNAME) in records

    def test_exception(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        with pytest.raises(command_watcher.CommandWatcherError):
            watch.run(self.cmd_stderr)

    def test_ignore_exceptions(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        process = watch.run(self.cmd_stderr, ignore_exceptions=[1])
        assert process.subprocess.returncode == 1

    def test_ignore_exceptions_raise(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        with pytest.raises(command_watcher.CommandWatcherError):
            watch.run(os.path.join(DIR_FILES, "exit-2.sh"), ignore_exceptions=[1])


class TestClassWatchMethodFinalReport:
    def final_report(self, **data: Any) -> Message:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        watch._timer.result = mock.Mock()  # type: ignore
        watch._timer.result.return_value = "11.123s"  # type: ignore
        return watch.final_report(**data)

    def test_without_arguments(self) -> None:
        message = self.final_report()
        assert message.status == 0
        assert message.message == "# TEST OK"
        assert message.message_monitoring == "TEST OK | execution_time=11.123s"

    def test_with_arguments(self) -> None:
        message = self.final_report(status=1, custom_message="test")
        assert message.status == 1
        assert message.message == "# TEST WARNING - test"
