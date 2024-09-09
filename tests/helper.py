import os
from pathlib import Path

DIR_FILES = Path(__file__).resolve().parent / "files"
"""Directory ``tests/files``"""

CONF = os.path.join(DIR_FILES, "conf.ini")
