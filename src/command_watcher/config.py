from pathlib import Path
from typing import Optional, Union

import yaml
from pretiac.config import Config as IcingaConfig
from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass


@dataclass
class EmailConfig:
    to_addr: str
    """The email address of the recipient."""

    smtp_login: str
    """The SMTP login name."""

    smtp_password: str
    """The SMTP password."""

    smtp_server: str
    """The URL of the SMTP server, for example: `smtp.example.com:587`."""

    to_addr_critical: str
    """The email address of the recipient to send critical messages to."""

    from_addr: str
    """The email address of the sender."""


@dataclass
class BeepConfig:
    activated: bool
    """"Activate the beep channel to report auditive messages."""


@dataclass
class Config:
    email: Optional[EmailConfig] = None

    icinga: Optional[IcingaConfig] = None

    beep: Optional[BeepConfig] = None


_config: Optional[Config] = None


def load_config(config_file: Optional[Union[str, Path]] = None) -> Config:
    if config_file is None:
        config_file = "/etc/command-watcher.yml"
    global _config
    if _config is None:
        adapter = TypeAdapter(Config)
        with open(config_file, "r") as file:
            config_raw = yaml.safe_load(file)
        _config = adapter.validate_python(config_raw)
    return _config
