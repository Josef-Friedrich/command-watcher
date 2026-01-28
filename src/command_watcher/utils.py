"""Small utility functions."""

import os
import pwd
import shutil
import socket
import stat
import urllib.request

HOSTNAME = socket.gethostname()
USERNAME = pwd.getpwuid(os.getuid()).pw_name


def download(url: str, dest: str) -> None:
    """Download a file and save it under a destination path.

    :param url: The URL of the file to download.
    :param dest: The path of the destination file.
    """
    with urllib.request.urlopen(url) as response, open(dest, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def make_executable(path: str) -> None:
    """Make a file executable.

    :param path: The path of the file
    """
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)
