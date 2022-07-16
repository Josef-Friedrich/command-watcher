"""
Module to watch the execution of shell scripts. Both streams (`stdout` and
`stderr`) are captured.
"""

from __future__ import annotations

import queue
import shlex
import shutil
import subprocess
import threading
import time
from importlib import metadata
from typing import (IO, Any, Dict, List, Literal, Optional, Sequence, Tuple,
                    TypedDict, Union)

from conf2levels import ClassInterface, ConfigReader, Spec
from typing_extensions import Unpack

from .log import ExtendedLogger, LoggingHandler, setup_logging
from .report import (HOSTNAME, BaseChannel, BeepChannel, EmailChannel,
                     IcingaChannel, Message, MessageParams,
                     MinimalMessageParams, Status, reporter)

__version__: str = metadata.version('command_watcher')

Stream = Literal['stdout', 'stderr']


class CommandWatcherError(Exception):
    """Exception raised by this module."""

    def __init__(self, msg: str, **data: Unpack[MessageParams]):
        reporter.report(
            status=2,
            custom_message='{}: {}'.format(self.__class__.__name__, msg),
            **data,  # type: ignore
        )


class Timer:
    """Measure the execution time of a command run."""

    def __init__(self) -> None:
        self.stop = 0
        """"The time when the timer stops. (UNIX timestamp)"""

        self.start = time.time()
        """"The start time. (UNIX timestamp)"""

        self.interval = 0
        """The time interval between start and stop."""

    def result(self) -> str:
        """
        Measure the time intervale

        :return: A formatted string displaying the result."""
        self.stop = time.time()
        self.interval = self.stop - self.start
        return '{:.3f}s'.format(self.interval)


# Configuration ###############################################################

CONF_DEFAULTS = {
    'email': {
        'subject_prefix': 'command_watcher',
    },
    'nsca': {
        'port': 5667,
    },
}


CONFIG_READER_SPEC: Spec = {
    'email': {
        'from_addr': {
            'description': 'The email address of the sender.',
        },
        'to_addr': {
            'description': 'The email address of the recipient.',
            'not_empty': True,
        },
        'to_addr_critical': {
            'description': 'The email address of the recipient to send '
                           'critical messages to.',
            'default': None,
        },
        'smtp_login': {
            'description': 'The SMTP login name.',
            'not_empty': True,
        },
        'smtp_password': {
            'description': 'The SMTP password.',
            'not_empty': True,
        },
        'smtp_server': {
            'description': 'The URL of the SMTP server, for example: '
                           '`smtp.example.com:587`.',
            'not_empty': True,
        },
    },
    'nsca': {
        'remote_host': {
            'description': 'The IP address of the NSCA remote host.',
            'not_empty': True,
        },
        'password': {
            'description': 'The NSCA password.',
            'not_empty': True,
        },
        'encryption_method': {
            'description': 'The NSCA encryption method. The supported '
                           'encryption methods are: 0 1 2 3 4 8 11 14 15 16',
            'not_empty': True,
        },
        'port': {
            'description': 'The NSCA port.',
            'default': 5667,
        },
    },
    'icinga': {
        'url': {
            'description': 'The HTTP URL. /v1/actions/process-check-result '
                           'is appended.',
            'not_empty': True,
        },
        'user': {
            'description': 'The user for the HTTP authentification.',
            'not_empty': True,
        },
        'password': {
            'description': 'The password for the HTTP authentification.',
            'not_empty': True,
        },
    },
    'beep': {
        'activated': {
            'description': 'Activate the beep channel to report auditive '
                           'messages.',
            'default': False,
        }
    }
}


# Main code ###################################################################

Args = Union[str, List[str], Tuple[str]]


class ProcessArgs(TypedDict, total=False):
    shell: bool
    """If true, the command will be executed through the
        shell.
    """

    cwd: str
    """Sets the current directory before the child is
        executed."""

    env: Dict[str, Any]
    """Defines the environment variables for the new process."""


class Process:
    """Run a process.

    You can use all keyword arguments from
    :py:class:`subprocess.Popen` except `bufsize`, `stderr`, `stdout`.

    :param args: List, tuple or string. A sequence of
        process arguments, like `subprocess.Popen(args)`.
    """
    args: Args
    """Process arguments in various types."""

    _queue: 'queue.Queue[Optional[Tuple[bytes, Stream]]]'

    log: ExtendedLogger
    """A ready to go and configured logger."""

    log_handler: LoggingHandler

    subprocess: subprocess.Popen[Any]

    def __init__(self, args: Args,
                 master_logger: Optional[ExtendedLogger] = None,
                 **kwargs: Unpack[ProcessArgs]):
        # self.args: typing.Union[str, list, tuple] = args
        self.args = args

        self._queue = queue.Queue()

        log, log_handler = setup_logging(master_logger=master_logger)
        self.log = log
        self.log_handler = log_handler

        self.log.info('Run command: {}'.format(' '.join(self.args_normalized)))
        timer = Timer()
        self.subprocess = subprocess.Popen(
            self.args_normalized,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # RuntimeWarning: line buffering (buffering=1) isn't
            # supported in binary mode, the default buffer size will be used
            # bufsize=1,
            **kwargs
        )

        self._start_thread(self.subprocess.stdout, 'stdout')
        self._start_thread(self.subprocess.stderr, 'stderr')

        for _ in range(2):
            for line, stream in iter(self._queue.get, None):
                if line:
                    line = line.decode('utf-8').strip()

                if line:
                    if stream == 'stderr':
                        self.log.stderr(line)
                    if stream == 'stdout':
                        self.log.stdout(line)
        self.subprocess.wait()
        self.log.info('Execution time: {}'.format(timer.result()))

    @property
    def args_normalized(self) -> Sequence[str]:
        """Normalized `args`, always a list"""
        if isinstance(self.args, str):
            return shlex.split(self.args)
        else:
            return self.args

    @property
    def stdout(self) -> str:
        """Alias / shortcut for `self.log_handler.stdout`."""
        return self.log_handler.stdout

    @property
    def line_count_stdout(self) -> int:
        """The count of lines of the current `stderr`."""
        return len(self.stdout.splitlines())

    @property
    def stderr(self) -> str:
        """Alias / shortcut for `self.log_handler.stderr`."""
        return self.log_handler.stderr

    @property
    def line_count_stderr(self) -> int:
        """The count of lines of the current `stderr`."""
        return len(self.stderr.splitlines())

    def _stdout_stderr_reader(self, pipe: IO[bytes],
                              stream: Stream) -> None:
        """
        :param object pipe: `process.stdout` or `process.stdout`
        """
        try:
            with pipe:
                for line in iter(pipe.readline, b''):
                    self._queue.put((line, stream))
        finally:
            self._queue.put(None)

    def _start_thread(self, pipe: Optional[IO[str]],
                      stream: Stream) -> None:
        """
        :param object pipe: `process.stdout` or `process.stdout`
        """
        threading.Thread(
            target=self._stdout_stderr_reader,
            args=[pipe, stream]
        ).start()


class Watch:
    """Watch the execution of a command. Capture all output of a command.
    provide and setup a logging facility.

    :param config_file: The file path of the configuration file in the INI
      format.
    :param service_name: A name of the watched service.
    :param raise_exceptions: Raise exceptions if `watch.run()` exists with a
      non-zero exit code.
    :param config_reader: A custom configuration reader. Specify this
      parameter to not use the build in configuration reader.
    """

    _hostname: str
    """The hostname of machine the watcher running on."""

    _service_name: str
    """A name of the watched service."""

    log: ExtendedLogger
    """A ready to go and configured logger."""

    _log_handler: LoggingHandler

    processes: List[Process]
    """A list of completed processes
    :py:class:`Process`. Everytime you use the method
    `run()` the process object is appened in the list."""

    _conf: Optional[ClassInterface]

    _raise_exceptions: bool
    """Raise exceptions"""

    _timer: Timer

    def __init__(self, config_file: Optional[str] = None,
                 service_name: str = 'command_watcher',
                 raise_exceptions: bool = True,
                 config_reader: Optional[ConfigReader] = None,
                 report_channels: Optional[List[BaseChannel]] = None):
        self._hostname = HOSTNAME

        self._service_name = service_name

        log, log_handler = setup_logging()

        self.log = log
        self.log.info('Hostname: {}'.format(self._hostname))

        self._log_handler = log_handler

        self._conf = None

        if not config_reader and config_file:
            config_reader = ConfigReader(
                spec=CONFIG_READER_SPEC,
                ini=config_file,
                dictionary=CONF_DEFAULTS,
            )

        if not config_reader:
            raise Exception('No config_reader object')

        self._conf = config_reader.get_class_interface()

        if report_channels is None:
            try:
                config_reader.check_section('email')
                email_reporter = EmailChannel(
                    smtp_server=self._conf.email.smtp_server,
                    smtp_login=self._conf.email.smtp_login,
                    smtp_password=self._conf.email.smtp_password,
                    to_addr=self._conf.email.to_addr,
                    from_addr=self._conf.email.from_addr,
                    to_addr_critical=self._conf.email.to_addr_critical,
                )
                reporter.add_channel(email_reporter)
                self.log.debug(email_reporter)
            except (ValueError, KeyError):
                pass

            try:
                config_reader.check_section('icinga')
                icinga_reporter = IcingaChannel(
                    url=self._conf.icinga.url,
                    user=self._conf.icinga.user,
                    password=self._conf.icinga.password,
                    service_name=self._service_name,
                )
                reporter.add_channel(icinga_reporter)
                self.log.debug(icinga_reporter)
            except (ValueError, KeyError):
                pass

            if shutil.which('beep') and self._conf.beep.activated:
                beep_reporter = BeepChannel()
                reporter.add_channel(beep_reporter)
                self.log.debug(beep_reporter)

        else:
            reporter.channels = []

        self.processes = []

        self._raise_exceptions = raise_exceptions

        self._timer = Timer()

    @property
    def stdout(self):
        """Alias / shortcut for `self._log_handler.stdout`."""
        return self._log_handler.stdout

    @property
    def stderr(self):
        """Alias / shortcut for `self._log_handler.stderr`."""
        return self._log_handler.stderr

    def run(self,
            args: Args,
            log: bool = True,
            ignore_exceptions: List[int] = [],
            **kwargs: Unpack[ProcessArgs]) -> Process:
        """
        Run a process.

        :param args: List, tuple or string. A sequence of
          process arguments, like `subprocess.Popen(args)`.
        :param log: Log the `stderr` and the `stdout` of the
          process. If false the `stdout` and the `stderr` are logged only
          to the local process logger, not to get global master logger.
        :param ignore_exceptions: A list of none-zero exit codes, which is
          ignored by this method.
        """
        if log:
            master_logger = self.log
        else:
            master_logger = None
        process = Process(args, master_logger=master_logger, **kwargs)
        self.processes.append(process)
        rc = process.subprocess.returncode
        if self._raise_exceptions and rc != 0 and rc not in ignore_exceptions:
            raise CommandWatcherError(
                'The command \'{}\' exists with an non-zero return code ({}).'
                .format(' '.join(process.args_normalized), rc),
                service_name=self._service_name,
                log_records=self._log_handler.all_records,
            )
        return process

    def report(self, status: Status,
               **data: Unpack[MinimalMessageParams]) -> Message:
        """Report a message using the preconfigured channels.
        """
        message = reporter.report(
            status=status,
            service_name=self._service_name,
            log_records=self._log_handler.all_records,
            processes=self.processes,
            **data,
        )
        self.log.debug(message)
        return message

    def final_report(self, **data: Unpack[MessageParams]) -> Message:
        """The same as the `report` method. Adds `execution_time` to the
        `performance_data`.
        """
        timer_result = self._timer.result()
        self.log.info(
            'Overall execution time: {}'.format(timer_result)
        )
        status = data.get('status', 0)
        data_dict: Dict[str, Any] = dict(data)
        if 'performance_data' not in data_dict:
            data_dict['performance_data'] = {}
        data_dict['performance_data']['execution_time'] = timer_result
        if 'status' in data_dict:
            del data_dict['status']
        return self.report(status=status, **data_dict)
