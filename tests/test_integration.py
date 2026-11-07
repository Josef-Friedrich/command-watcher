from command_watcher import Watch
from tests.helper import CONF, DIR_FILES


class TestIntegration:
    def test_run_stderr_script_and_report_critical(self) -> None:
        watch = Watch(
            config_file=CONF,
            service_name="log_stderr",
            report_channels=[],
        )

        script = DIR_FILES / "stderr.sh"

        process = watch.run(str(script), ignore_exceptions=[1])

        assert process.subprocess.returncode == 1
        assert process.stderr == "One line to stderr!"

        message = watch.final_report(status=2)
        assert message.status == 2
        assert message.status_text == "CRITICAL"
