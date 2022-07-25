import os
import unittest
from unittest import mock

from stdout_stderr_capturing import Capturing

import command_watcher
from command_watcher import Args, Watch
from command_watcher.report import HOSTNAME, USERNAME

from .helper import CONF, DIR_FILES


class TestClassProcess(unittest.TestCase):
    def setUp(self) -> None:
        self.cmd_stderr = os.path.join(DIR_FILES, "stderr.sh")
        self.cmd_stdout = os.path.join(DIR_FILES, "stdout.sh")

    def launch_process(self, args: Args):
        return command_watcher.Process(args)

    def test_attribute_args(self) -> None:
        process = self.launch_process("ls -l")
        self.assertEqual(process.args, "ls -l")

    def test_attribute_log(self) -> None:
        process = self.launch_process("ls -l")
        self.assertEqual(process.log.__class__.__name__, "Logger")

    def test_attribute_log_handler(self) -> None:
        process = self.launch_process("ls -l")
        self.assertEqual(process.log_handler.__class__.__name__, "LoggingHandler")

    def test_attribute_subprocess(self) -> None:
        process = self.launch_process("ls -l")
        self.assertEqual(process.subprocess.__class__.__name__, "Popen")

    def test_property_args_normalized(self) -> None:
        process = self.launch_process("ls -l")
        self.assertEqual(process.args_normalized, ["ls", "-l"])

    def test_property_stdout(self) -> None:
        process = self.launch_process([self.cmd_stdout])
        self.assertTrue(process.stdout)

    def test_property_line_count_stdout(self) -> None:
        process = self.launch_process([self.cmd_stdout])
        self.assertEqual(process.line_count_stdout, 1)
        self.assertEqual(process.line_count_stderr, 0)

    def test_property_stderr(self) -> None:
        process = self.launch_process([self.cmd_stderr])
        self.assertTrue(process.stderr)

    def test_property_line_count_stderr(self) -> None:
        process = self.launch_process([self.cmd_stderr])
        self.assertEqual(process.line_count_stdout, 0)
        self.assertEqual(process.line_count_stderr, 1)


class TestClassWatch(unittest.TestCase):
    def setUp(self) -> None:
        self.cmd_stderr = os.path.join(DIR_FILES, "stderr.sh")
        self.cmd_stdout = os.path.join(DIR_FILES, "stdout.sh")

    def test_argument_config_file(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        self.assertEqual(watch._conf.email.to_addr, "to@example.com")

    def test_method_run_output_stdout(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        with Capturing() as output:
            process = watch.run(self.cmd_stdout)
        self.assertEqual(process.subprocess.returncode, 0)
        self.assertEqual(len(output), 3)
        self.assertIn("STDOUT", output[1])
        self.assertIn("One line to stdout!", output[1])
        self.assertIn("Execution time: ", output[2])

    def test_method_run_output_stderr(self) -> None:
        watch = Watch(
            config_file=CONF,
            service_name="test",
            raise_exceptions=False,
        )
        with Capturing(stream="stderr") as output:
            process = watch.run(self.cmd_stderr)
        self.assertEqual(process.subprocess.returncode, 1)
        # On travis
        # ['Exception in thread Thread-59:', 'Trace[993 chars][0m'] != ''
        # self.assertEqual(len(output), 1)
        self.assertIn("STDERR", output.tostring())
        self.assertIn("One line to stderr!", output.tostring())

    def test_method_run_multiple(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        watch.run(self.cmd_stdout)
        watch.run(self.cmd_stderr)
        self.assertEqual(len(watch._log_handler.buffer), 9)
        self.assertIn("Hostname: ", watch._log_handler.all_records)

    def test_method_run_log_true(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        process = watch.run(self.cmd_stdout, log=True)
        self.assertEqual(watch.stdout, "One line to stdout!")
        self.assertEqual(process.stdout, "One line to stdout!")

    def test_method_run_log_false(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", raise_exceptions=False)
        process = watch.run(self.cmd_stdout, log=False)
        self.assertEqual(watch.stdout, "")
        self.assertEqual(process.stdout, "One line to stdout!")

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
        with self.assertRaises(TypeError):
            watch.run("ls", xxx=False)

    def test_property_service_name(self) -> None:
        watch = Watch(config_file=CONF, service_name="Service")
        self.assertEqual(watch._service_name, "Service")

    def test_property_hostname(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        self.assertEqual(watch._hostname, HOSTNAME)

    def test_property_stdout(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        watch.log.stdout("stdout")
        self.assertEqual(watch.stdout, "stdout")

    def test_property_stderr(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        watch.log.stderr("stderr")
        self.assertEqual(watch.stderr, "stderr")

    def test_propertyprocesses(self) -> None:
        watch = Watch(config_file=CONF, service_name="test")
        self.assertEqual(watch.processes, [])
        watch.run(["ls"])
        watch.run(["ls", "-l"])
        watch.run(["ls", "-la"])
        self.assertEqual(len(watch.processes), 3)

    def test_method_report_channel_email(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        watch.log.info("info")
        watch.run("ls")

        with mock.patch("command_watcher.icinga.send_passive_check"), mock.patch(
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
        self.assertEqual(call_args[0], "from@example.com")
        self.assertEqual(call_args[1], ["to@example.com"])
        self.assertIn("From: from@example.com\nTo: to@example.com\n", call_args[2])

    def test_method_report_channel_email_critical(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        with mock.patch("command_watcher.icinga.send_passive_check"), mock.patch(
            "smtplib.SMTP"
        ) as SMTP:
            watch.report(status=2)
        server = SMTP.return_value
        call_args = server.sendmail.call_args[0]
        self.assertEqual(call_args[1], ["critical@example.com"])
        self.assertIn(
            "From: from@example.com\nTo: critical@example.com\n", call_args[2]
        )

    def test_method_report_channel_nsca(self) -> None:
        watch = Watch(config_file=CONF, service_name="my_service")
        with mock.patch(
            "command_watcher.icinga.send_passive_check"
        ) as send_passive_check, mock.patch("command_watcher.report.send_email"):
            watch.report(
                status=0,
                custom_message="My message",
                performance_data={"perf_1": 1, "perf_2": "test"},
                prefix="",
            )
        send_passive_check.assert_called_with(
            url="1.2.3.4",
            user="u",
            password=1234,
            status=0,
            host_name=HOSTNAME,
            service_name="my_service",
            text_output="MY_SERVICE OK - My message",
            performance_data="perf_1=1 perf_2=test",
        )

        records = watch._log_handler.all_records
        self.assertIn("DEBUG [Message]", records)
        self.assertIn("custom_message: 'My message',", records)
        self.assertIn("message: 'MY_SERVICE OK - My message',", records)
        self.assertIn(
            "message_monitoring: 'MY_SERVICE OK - My message | "
            "perf_1=1 perf_2=test',",
            records,
        )
        self.assertIn("performance_data: 'perf_1=1 perf_2=test'", records)
        self.assertIn("service_name: 'my_service',", records)
        self.assertIn("status_text: 'OK',", records)
        self.assertIn("user: '[user:{}]'".format(USERNAME), records)

    def test_exception(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        with self.assertRaises(command_watcher.CommandWatcherError):
            watch.run(self.cmd_stderr)

    def test_ignore_exceptions(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        process = watch.run(self.cmd_stderr, ignore_exceptions=[1])
        self.assertEqual(process.subprocess.returncode, 1)

    def test_ignore_exceptions_raise(self) -> None:
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        with self.assertRaises(command_watcher.CommandWatcherError):
            watch.run(os.path.join(DIR_FILES, "exit-2.sh"), ignore_exceptions=[1])


class TestClassWatchMethodFinalReport(unittest.TestCase):
    def final_report(self, **data):
        watch = Watch(config_file=CONF, service_name="test", report_channels=[])
        watch._timer.result = mock.Mock()
        watch._timer.result.return_value = "11.123s"
        return watch.final_report(**data)

    def test_without_arguments(self) -> None:
        message = self.final_report()
        self.assertEqual(message.status, 0)
        self.assertEqual(message.message, "[cwatcher]: TEST OK")
        self.assertEqual(
            message.message_monitoring, "[cwatcher]: TEST OK | execution_time=11.123s"
        )

    def test_with_arguments(self) -> None:
        message = self.final_report(status=1, custom_message="test")
        self.assertEqual(message.status, 1)
        self.assertEqual(message.message, "[cwatcher]: TEST WARNING - test")
