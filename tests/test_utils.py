import os
import stat
import tempfile
import unittest

from command_watcher.utils import download, make_executable


class TestUtils(unittest.TestCase):

    def test_download(self):
        url = 'https://raw.githubusercontent.com/' \
              'Josef-Friedrich/command-watcher/main/README.rst'
        dest = tempfile.mkstemp()[1]
        download(url, dest)

        self.assertTrue(os.path.exists(dest))

        with open(dest, 'r') as dest_file:
            content = dest_file.read()

        self.assertIn('command_watcher', content)

    def test_make_executable(self):
        tmp = tempfile.mkstemp()
        tmp_file = tmp[1]
        with open(tmp_file, 'w') as tmp_fd:
            tmp_fd.write('test')

        self.assertFalse(stat.S_IXUSR & os.stat(tmp_file)[stat.ST_MODE])

        make_executable(tmp_file)
        self.assertTrue(stat.S_IXUSR & os.stat(tmp_file)[stat.ST_MODE])
