import pytest

from command_watcher import Watch
from tests.helper import DIR_FILES


class TestIntegration:
    @pytest.mark.skip
    def test_download(self) -> None:
        watch = Watch(config_file="/etc/command-watcher.yml", service_name="log_stderr")

        script = DIR_FILES / "stderr.sh"

        watch.run(str(script))

        watch.final_report(status=2)
