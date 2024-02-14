import os
import stat
import tempfile

from command_watcher.utils import download, make_executable


class TestUtils:
    def test_download(self) -> None:
        url = (
            "https://raw.githubusercontent.com/"
            "Josef-Friedrich/command-watcher/main/README.rst"
        )
        dest = tempfile.mkstemp()[1]
        download(url, dest)

        assert os.path.exists(dest)

        with open(dest, "r") as dest_file:
            content = dest_file.read()

        assert "command_watcher" in content

    def test_make_executable(self) -> None:
        tmp = tempfile.mkstemp()
        tmp_file = tmp[1]
        with open(tmp_file, "w") as tmp_fd:
            tmp_fd.write("test")

        assert not stat.S_IXUSR & os.stat(tmp_file)[stat.ST_MODE]

        make_executable(tmp_file)
        assert stat.S_IXUSR & os.stat(tmp_file)[stat.ST_MODE]
